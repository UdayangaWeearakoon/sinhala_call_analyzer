import logging
import os

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