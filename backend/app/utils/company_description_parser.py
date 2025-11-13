"""LLM-powered parser for extracting company insights from descriptions."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Sequence

from loguru import logger
from ollama import Client

from app.config import settings


@dataclass(frozen=True)
class CompanyDescriptionInsights:
    """Lightweight container for facts derived from a company description."""

    has_own_products: bool | None = None
    is_recruiting_company: bool | None = None


LLM_SYSTEM_PROMPT = """You are an analyst who classifies companies based on their descriptions.

Output ONLY a JSON object with this EXACT structure:
{
  "has_own_products": true|false|null,
  "is_recruiting_company": true|false|null
}

Definition guidelines:
- has_own_products: true when the description clearly states the company builds or sells its own software/platform/product. false when it explicitly only provides services built on other vendors' products (e.g., pure consulting or staffing firms). null when there isn't enough information.
- is_recruiting_company: true when the description indicates staffing, recruiting, talent placement, or headhunting services. false when the company is clearly a product or service company that is NOT a staffing/recruiting firm. null when unclear.

When uncertain, prefer null instead of guessing. Do not include any explanation or additional fields."""

LLM_USER_PROMPT = """Company Description:
{description}

Return ONLY the JSON object."""


def parse_company_description(
    description: str | None,
    *,
    model_name: str = "qwen3:14b",
    timeout: int = 120,
    ollama_url: str | None = None,
    use_json_format: bool = False,
    fallback_to_heuristics: bool = True,
    client: Client | None = None,
) -> CompanyDescriptionInsights:
    """
    Parse company description text with an Ollama LLM to derive insight booleans.

    Falls back to lightweight heuristics when the LLM is unreachable or returns invalid JSON.
    """
    if not description or not description.strip():
        return CompanyDescriptionInsights()

    normalized_description = " ".join(description.split())

    base_url = ollama_url or settings.OLLAMA_SERVER_URL
    llm_client = client
    if llm_client is None:
        llm_client = Client(host=base_url, timeout=timeout)

    prompt = LLM_USER_PROMPT.format(description=normalized_description)
    full_prompt = f"{LLM_SYSTEM_PROMPT}\n\n{prompt}"

    params: dict[str, Any] = {
        "model": model_name,
        "prompt": full_prompt,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_ctx": 2048,
        },
    }
    if use_json_format:
        params["format"] = "json"

    try:
        response = llm_client.generate(**params)
        raw_text = _extract_response_text(response)
        insights = _insights_from_raw_text(raw_text)
        if insights:
            logger.info("Derived company insights via Ollama model %s", model_name)
            return insights
        logger.warning("Ollama returned unparsable content for company description.")
    except Exception as exc:  # noqa: BLE001 - need to handle network/Ollama errors uniformly
        logger.exception("Failed to parse company description via Ollama: %s", exc)

    if fallback_to_heuristics:
        logger.info("Falling back to heuristic company description parsing.")
        return _heuristic_company_insights(normalized_description)

    return CompanyDescriptionInsights()


def _extract_response_text(response: Any) -> str:
    if hasattr(response, "response"):
        return response.response or ""
    if isinstance(response, dict):
        return response.get("response", "") or ""
    return ""


def _insights_from_raw_text(raw_text: str) -> CompanyDescriptionInsights | None:
    if not raw_text:
        return None

    candidate = _strip_code_fence(raw_text.strip())
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        logger.error("Company description LLM response is not valid JSON: %s", raw_text)
        return None

    has_own_products = _coerce_optional_bool(payload.get("has_own_products"))
    is_recruiting_company = _coerce_optional_bool(payload.get("is_recruiting_company"))

    if has_own_products is None and is_recruiting_company is None:
        return None

    return CompanyDescriptionInsights(
        has_own_products=has_own_products,
        is_recruiting_company=is_recruiting_company,
    )


def _strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        stripped = text.split("\n", 1)[1] if "\n" in text else ""
        if stripped.endswith("```"):
            stripped = stripped.rsplit("```", 1)[0]
        return stripped.strip()
    return text


def _coerce_optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes"}:
            return True
        if lowered in {"false", "no"}:
            return False
        if lowered in {"null", "none", ""}:
            return None
    return None


# --- Heuristic fallback ----------------------------------------------------


def _compile_patterns(patterns: Sequence[str]) -> list[re.Pattern[str]]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


_PRODUCT_STRONG_PATTERNS = _compile_patterns(
    [
        r"\bwe (?:build|develop|ship|deliver|maintain)\b.*\b(?:platform|product|software|technology|application)s?\b",
        r"\bour (?:flagship|core)\s+(?:platform|product|solution)",
        r"\bsoftware-as-a-service\b",
        r"\bsaas\b",
        r"\bproprietary (?:technology|platform|product)\b",
    ]
)

_PRODUCT_SUPPORT_PATTERNS = _compile_patterns(
    [
        r"\bplatform\b",
        r"\bproduct\b",
        r"\bapplication\b",
        r"\bsoftware\b",
        r"\bmobile app\b",
        r"\bapi\b",
        r"\btool\b",
        r"\bdigital solution\b",
        r"\bdata platform\b",
    ]
)

_RECRUITING_STRONG_PATTERNS = _compile_patterns(
    [
        r"\bstaff(?:ing| augmentation)\b",
        r"\brecruit(?:er|ing|ment)\b (?:agency|firm|services|solutions|partner)",
        r"\btalent acquisition\b",
        r"\bplacement (?:services|firm|agency)\b",
        r"\bheadhunt(?:ers|ing)?\b",
        r"\bexecutive search\b",
        r"\brpo\b",
    ]
)

_RECRUITING_SUPPORT_PATTERNS = _compile_patterns(
    [
        r"\brecruit(?:ing|ment)\b",
        r"\btalent\b",
        r"\bhiring solutions\b",
        r"\bstaff augmentation\b",
        r"\bcontract staffing\b",
    ]
)


def _heuristic_company_insights(description: str) -> CompanyDescriptionInsights:
    strong_product_signal = _matches_any(_PRODUCT_STRONG_PATTERNS, description)
    product_score = _score_matches(_PRODUCT_SUPPORT_PATTERNS, description)

    strong_recruiting_signal = _matches_any(_RECRUITING_STRONG_PATTERNS, description)
    recruiting_score = _score_matches(_RECRUITING_SUPPORT_PATTERNS, description)

    has_own_products: bool | None = None
    if strong_product_signal or product_score >= 2:
        has_own_products = True
    elif strong_recruiting_signal and product_score == 0:
        has_own_products = False

    is_recruiting_company: bool | None = None
    if strong_recruiting_signal or recruiting_score >= 2:
        is_recruiting_company = True
    elif has_own_products:
        is_recruiting_company = False

    return CompanyDescriptionInsights(
        has_own_products=has_own_products,
        is_recruiting_company=is_recruiting_company,
    )


def _matches_any(patterns: Sequence[re.Pattern[str]], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _score_matches(patterns: Sequence[re.Pattern[str]], text: str) -> int:
    return sum(1 for pattern in patterns if pattern.search(text))


__all__ = ["CompanyDescriptionInsights", "parse_company_description"]
