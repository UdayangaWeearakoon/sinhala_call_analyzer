import logging
import os

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

logger = logging.getLogger(__name__)

MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "256"))

CLASSIFICATION_FRAMEWORK = """
Analyze the call transcript (English, Sinhala, or Singlish) and output the single best category based on the primary intent.

Categories:
- Billing: Balances, arrears, app payment updates, SMS billing requests.
- Fault Reporting: Malfunctioning services (e.g., Peo TV disconnected, missing channels) requiring a logged ticket.
- Products: Package updates/upgrades, base data allowances, third-party app payments/refunds.
- Technical Assistance (TA): Over-the-phone troubleshooting (e.g., box power cycles, router/Wi-Fi configuration).
- Directory Inquiries (DQ): Requests for phone numbers, addresses, or locations of businesses/entities.
- Extra GB (GB) services: Data balance checks or explicit Extra GB add-on activation/purchases.

Rules:
- Classify by the primary goal of the caller.
- Respond ONLY with a JSON object: {"category": "<category>", "confidence": <float 0.0-1.0>}
- Do NOT include any text outside the JSON object.
"""

SYSTEM_INSTRUCTION = "You are a call transcript classifier." + CLASSIFICATION_FRAMEWORK



@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=120),
    retry=retry_if_exception(is_retryable),
)
def _call_api(client, prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt},
        ],
        max_tokens=MAX_TOKENS,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def classify(text: str) -> tuple[str, float]:
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )
    prompt = "Classify the following call transcript:\n\n" + text

    for attempt in range(2):
        try:
            content = _call_api(client, prompt)
        except Exception as exc:
            raise exc

        try:
            result = ClassificationResult.model_validate_json(content)
            return result.category, result.confidence
        except ValidationError as e:
            if attempt == 0:
                logger.warning("Schema validation failed (retry with stricter prompt): %s", e)
                prompt = (
                    "You MUST respond with valid JSON only. No markdown, no code fences, no explanation.\n"
                    'Format: {"category": "<category>", "confidence": <0.0-1.0>}\n\n'
                    "Transcript:\n" + text
                )
                continue
            logger.error("Schema validation failed after retry: %s", e)
            raise ClassificationSchemaError(
                f"Model returned invalid schema after retry: {e}"
            ) from e

    raise RuntimeError("Unexpected: classify fell through")

from typing import Literal
from pydantic import BaseModel, Field, ValidationError, field_validator

class CallAnalysisFields(BaseModel):
    category: Literal[
        "Billing",
        "Fault Reporting",
        "Products",
        "Technical Assistance",
        "Directory Inquiries",
        "Extra GB",
    ]
    customer_request: str
    resolution_status: Literal["Resolved", "Partially Resolved", "Not Resolved", "Unknown"]
    satisfaction: Literal["Satisfied", "Neutral", "Dissatisfied", "Unknown"]
    follow_up_required: bool
    call_summary: str
    resolution_evidence: str | None = None
    satisfaction_evidence: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    resolution_confidence: float = Field(ge=0.0, le=1.0)
    satisfaction_confidence: float = Field(ge=0.0, le=1.0)

class ClassificationResult(CallAnalysisFields):
    pass

class BatchClassificationItem(CallAnalysisFields):
    id: str
    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, value):
        return str(value)

class BatchClassificationResponse(BaseModel):
    results: list[BatchClassificationItem]

class ClassificationSchemaError(Exception):
    """Raised when the model returns invalid JSON/schema after retry attempt."""
    pass