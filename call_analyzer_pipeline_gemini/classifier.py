import json
import logging
import os

from openai import OpenAI
from pydantic import BaseModel, ValidationError, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

logger = logging.getLogger(__name__)

MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")

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

BATCH_ITEM_TEMPLATE = "--- ID: {id} ---\n{text}"

BATCH_PROMPT_TEMPLATE = (
    "Classify the following call transcripts. "
    "Output a JSON array where each element has the transcript's id, "
    "its category, and a confidence score.\n\n"
    "{items}\n\n"
    'Return ONLY a valid JSON array: '
    '[{{"id": "<id>", "category": "<category>", "confidence": 0.0}}]'
)

STRICTER_BATCH_PROMPT = (
    "You MUST respond with valid JSON only. No markdown, no code fences, no explanation.\n"
    'Format: [{{"id": "<id>", "category": "<category>", "confidence": 0.0}}]\n\n'
    "Transcripts:\n{items}"
)


class ClassificationResult(BaseModel):
    category: str
    confidence: float


class BatchClassificationItem(BaseModel):
    id: str
    category: str
    confidence: float

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v):
        return str(v)


class ClassificationSchemaError(Exception):
    """Model returned invalid JSON after retry."""
    pass


def is_retryable(exc):
    from openai import APIStatusError, APIConnectionError, APITimeoutError
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code in (429, 500, 502, 503):
        return True
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    return False


MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "256"))


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


def classify_transcript_batch(items: list[dict]) -> list[BatchClassificationItem]:
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )

    item_blocks = "\n\n".join(
        BATCH_ITEM_TEMPLATE.format(id=item["id"], text=item["text"])
        for item in items
    )
    prompt = BATCH_PROMPT_TEMPLATE.format(items=item_blocks)

    for attempt in range(2):
        try:
            content = _call_api(client, prompt)
        except Exception as exc:
            raise exc

        try:
            raw_list = json.loads(content)
            return [BatchClassificationItem.model_validate(item) for item in raw_list]
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == 0:
                logger.warning("Batch schema validation failed (retry with stricter prompt): %s", e)
                prompt = STRICTER_BATCH_PROMPT.format(items=item_blocks)
                continue
            logger.error("Batch schema validation failed after retry: %s", e)
            raise ClassificationSchemaError(
                f"Batch model returned invalid schema after retry: {e}"
            ) from e

    raise RuntimeError("Unexpected: classify_transcript_batch fell through")
