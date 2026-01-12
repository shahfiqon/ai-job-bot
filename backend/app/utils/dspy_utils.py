"""
DSPy utilities for extracting structured information from job descriptions.

This module provides reusable functions for analyzing job postings and extracting:
- Python-centric roles
- Fully remote positions
- Startup/small company opportunities
- 1099/freelance/contract arrangements
- Roles without clearance/fingerprinting/credit checks
- Required and preferred skills
- Required years of experience
- Key responsibilities
"""

import time
from typing import Optional

import dspy
from pydantic import BaseModel, Field

from app.config import settings


# Configuration constants
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 500


# Pydantic models for output schema
class FieldValue(BaseModel):
    """Value with confidence score for a single field."""

    value: Optional[bool | str | int | list[str]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class JobExtractionOutput(BaseModel):
    """Complete extraction output schema."""

    is_python_main: FieldValue
    contract_feasible: FieldValue
    relocate_required: FieldValue
    specific_locations: FieldValue
    accepts_non_us: FieldValue
    screening_required: FieldValue
    company_size: FieldValue
    required_skills: FieldValue
    preferred_skills: FieldValue
    required_years_experience: FieldValue
    responsibilities: FieldValue
    metadata: dict[str, float]


# DSPy signature for field extraction
class JobExtraction(dspy.Signature):
    """Extract structured information from job descriptions."""

    job_description: str = dspy.InputField(
        desc="Full text of the job description"
    )

    is_python_main: bool = dspy.OutputField(
        desc="True ONLY if Python is explicitly mentioned in the job description AND (Python is listed first/prominently OR 70%+ of mentioned technologies are Python-related). False if Python is not mentioned at all. Examples: 'Python Developer' (true), 'Full-stack: React, Node, TypeScript' (false - no Python mentioned), 'Backend: Python, Django, FastAPI, PostgreSQL' (true), 'TypeScript, React, PostgreSQL' (false - no Python mentioned)"
    )

    contract_feasible: bool = dspy.OutputField(
        desc="True if the job mentions contractors, 1099, C2C, freelance, or signals like 'flexible arrangement' or 'open to contractors'. Also true if multiple engagement types mentioned. False if 'W-2 only' or 'no contractors' is stated. Look for context clues but don't assume feasibility from silence."
    )

    relocate_required: bool = dspy.OutputField(
        desc="True ONLY if job explicitly states 'relocation required', 'must relocate', or 'must be based in [city]'. Do not infer from on-site requirements or office location mentions. Be conservative - only flag explicit relocation requirements."
    )

    specific_locations: str = dspy.OutputField(
        desc="Comma-separated list of specific US states, regions, or cities mentioned in the job (e.g., 'Texas, California'). Do NOT include generic 'USA' or 'Remote'. Include timezone requirements if mentioned (e.g., 'EST timezone'). Return empty string if only generic USA/Remote mentioned."
    )

    accepts_non_us: bool = dspy.OutputField(
        desc="True if job mentions 'global role', 'international', 'worldwide', or 'any location'. False if 'US only', 'must be in USA', or 'US work authorization required' is stated. Be conservative - assume US-only unless clearly stated otherwise."
    )

    screening_required: bool = dspy.OutputField(
        desc="True if job mentions ANY of: 'security clearance', 'background check', 'credit check', 'fingerprinting', 'drug screening', 'comprehensive screening'. Be aggressive - flag even standard background checks since user wants to avoid heavy screening processes."
    )

    company_size: str = dspy.OutputField(
        desc="Categorize as 'startup' (<20 employees, seed/Series A, 'founding team'), 'small' (20-200 employees, Series B), 'medium' (200-1000), 'large' (1000+, Fortune 500, big tech names), or 'unknown' if unclear. Look for employee counts, funding stage mentions, or company name recognition."
    )

    required_skills: list[str] = dspy.OutputField(
        desc="List of skills explicitly marked as required or mandatory in the job description. Extract specific technical skills, programming languages, tools, frameworks, or competencies that are stated as requirements. Return empty list if none are mentioned."
    )

    preferred_skills: list[str] = dspy.OutputField(
        desc="List of skills marked as preferred, nice-to-have, or bonus qualifications. These are skills that would be beneficial but are not mandatory. Return empty list if none are mentioned."
    )

    required_years_experience: int = dspy.OutputField(
        desc="The minimum number of years of experience required for the role. Extract numeric value from phrases like '5+ years', 'minimum 3 years', 'at least 7 years'. Return 0 if not specified or if only preferred experience is mentioned."
    )

    responsibilities: list[str] = dspy.OutputField(
        desc="List of key responsibilities, duties, or tasks mentioned in the job description. Extract main responsibilities as separate items. Each item should be a concise description of a key responsibility. Return empty list if none are mentioned."
    )


def _compute_confidence(value, field_name: str) -> float:
    """
    Heuristic confidence scoring based on value type and field.

    Args:
        value: The extracted value
        field_name: Name of the field (for potential field-specific logic)

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if value is None:
        return 0.0

    # For boolean fields, check if value is explicitly set
    if isinstance(value, bool):
        # High confidence for explicit boolean values
        return 0.85

    # For integer fields (required_years_experience)
    if isinstance(value, int):
        if value == 0:
            return 0.0  # 0 likely means "not specified"
        # High confidence for non-zero integer values
        return 0.85

    # For string fields (company_size, specific_locations)
    if isinstance(value, str):
        if value.lower() in ["unknown", ""]:
            return 0.0
        # Medium-high confidence for non-empty strings
        return 0.75

    # For list fields
    if isinstance(value, list):
        if len(value) == 0:
            return 0.60  # Medium confidence for empty list (explicitly checked)
        return 0.85  # High confidence for non-empty list

    return 0.5  # Default medium confidence


async def extract_job_info(
    job_description: str,
    endpoint: Optional[str] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """
    Extract structured information from job description using DSPy (async).

    Args:
        job_description: Full text of the job description as a string
        endpoint: OpenAI-compatible API endpoint URL. If None, uses settings.LLAMA_SERVER_URL + '/v1'
        temperature: Temperature setting for the LLM (default: 0.1)
        max_tokens: Maximum tokens for the LLM response (default: 500)

    Returns:
        Dictionary with extracted fields and confidence scores, following JobExtractionOutput schema

    Example:
        >>> result = await extract_job_info("We are looking for a Python developer...")
        >>> print(result["is_python_main"].value)
        True
    """
    start_time = time.time()

    # Determine endpoint URL
    if endpoint is None:
        endpoint = f"{settings.LLAMA_SERVER_URL}/v1"

    # Configure DSPy with OpenAI-compatible endpoint
    lm = dspy.LM(
        model="openai/default",  # llama.cpp uses "default" or model name
        api_base=endpoint,
        model_type="chat",
        api_key="not-needed",  # llama.cpp doesn't require auth
        temperature=temperature,
        max_tokens=max_tokens,
    )
    dspy.configure(lm=lm)

    # Create prediction instance and wrap with asyncify for async execution
    extractor = dspy.Predict(JobExtraction)
    async_extractor = dspy.asyncify(extractor)

    # Execute extraction asynchronously
    try:
        result = await async_extractor(job_description=job_description)
    except Exception as e:
        raise RuntimeError(f"Error during LLM extraction: {e}") from e

    processing_time = time.time() - start_time

    # Parse specific_locations string into array
    specific_locations_str = getattr(result, "specific_locations", "")
    specific_locations_list = []
    if specific_locations_str and specific_locations_str.strip():
        # Split by comma and clean up whitespace
        specific_locations_list = [
            loc.strip() for loc in specific_locations_str.split(",") if loc.strip()
        ]

    required_skills = [skill.lower() for skill in getattr(result, "required_skills", []) if isinstance(skill, str)]

    # Build output structure
    output = {
        "is_python_main": FieldValue(
            value=getattr(result, "is_python_main", False) and "python" in required_skills,
            confidence=_compute_confidence(getattr(result, "is_python_main", None), "is_python_main")
        ),
        "contract_feasible": FieldValue(
            value=getattr(result, "contract_feasible", None),
            confidence=_compute_confidence(getattr(result, "contract_feasible", None), "contract_feasible")
        ),
        "relocate_required": FieldValue(
            value=getattr(result, "relocate_required", None),
            confidence=_compute_confidence(getattr(result, "relocate_required", None), "relocate_required")
        ),
        "specific_locations": FieldValue(
            value=specific_locations_list,
            confidence=_compute_confidence(specific_locations_list, "specific_locations")
        ),
        "accepts_non_us": FieldValue(
            value=getattr(result, "accepts_non_us", None),
            confidence=_compute_confidence(getattr(result, "accepts_non_us", None), "accepts_non_us")
        ),
        "screening_required": FieldValue(
            value=getattr(result, "screening_required", None),
            confidence=_compute_confidence(getattr(result, "screening_required", None), "screening_required")
        ),
        "company_size": FieldValue(
            value=getattr(result, "company_size", "unknown"),
            confidence=_compute_confidence(getattr(result, "company_size", "unknown"), "company_size")
        ),
        "required_skills": FieldValue(
            value=getattr(result, "required_skills", []),
            confidence=_compute_confidence(getattr(result, "required_skills", []), "required_skills")
        ),
        "preferred_skills": FieldValue(
            value=getattr(result, "preferred_skills", []),
            confidence=_compute_confidence(getattr(result, "preferred_skills", []), "preferred_skills")
        ),
        "required_years_experience": FieldValue(
            value=getattr(result, "required_years_experience", None),
            confidence=_compute_confidence(getattr(result, "required_years_experience", None), "required_years_experience")
        ),
        "responsibilities": FieldValue(
            value=getattr(result, "responsibilities", []),
            confidence=_compute_confidence(getattr(result, "responsibilities", []), "responsibilities")
        ),
        "metadata": {
            "processing_time_seconds": round(processing_time, 2)
        }
    }

    return output
