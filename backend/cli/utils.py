from __future__ import annotations

import time
from datetime import date
from typing import Any, Iterable
from urllib.parse import urlparse, urlunparse

import pandas as pd
import requests
from loguru import logger

from app.config import settings
from app.models.company import Company
from app.models.job import Job
from app.schemas.structured_job import StructuredJobData
from app.utils.company_description_parser import parse_company_description

PROXYCURL_COMPANY_ENDPOINT = "https://enrichlayer.com/api/v2/company"


def fetch_company_from_proxycurl(
    linkedin_url: str,
    *,
    max_attempts: int = 3,
) -> dict[str, Any] | None:
    if not linkedin_url:
        return None

    api_key = settings.PROXYCURL_API_KEY
    if not api_key:
        logger.error("Proxycurl API key is missing; cannot enrich %s", linkedin_url)
        return None

    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"url": linkedin_url}

    backoff_delay = 1.0
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        try:
            response = requests.get(
                PROXYCURL_COMPANY_ENDPOINT,
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else "HTTP"
            if status_code == 401:
                logger.error("Proxycurl API key rejected for %s", linkedin_url)
                return None
            if status_code == 429:
                if attempt < max_attempts:
                    logger.warning(
                        "Proxycurl rate limit hit for %s; retrying in %ss "
                        "(attempt %s/%s)",
                        linkedin_url,
                        int(backoff_delay),
                        attempt,
                        max_attempts,
                    )
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                    continue
                logger.error(
                    "Proxycurl rate limit exceeded for %s after %s attempts",
                    linkedin_url,
                    attempt,
                )
                return None
            if status_code == 404:
                logger.warning("Proxycurl could not find company for %s", linkedin_url)
                return None
            logger.error(
                "Proxycurl HTTP error (%s) while enriching %s: %s",
                status_code,
                linkedin_url,
                exc,
            )
            return None
        except requests.RequestException as exc:
            logger.error("Proxycurl request failure for %s: %s", linkedin_url, exc)
            return None

    return None


def map_proxycurl_to_company(
    proxycurl_data: dict[str, Any],
    linkedin_url: str,
) -> Company:
    company_size = proxycurl_data.get("company_size") or []
    hq = proxycurl_data.get("hq") or {}
    description = proxycurl_data.get("description")
    description_insights = parse_company_description(description)

    return Company(
        linkedin_url=linkedin_url,
        linkedin_internal_id=proxycurl_data.get("linkedin_internal_id"),
        name=proxycurl_data.get("name") or "Unknown",
        description=description,
        has_own_products=description_insights.has_own_products,
        is_recruiting_company=description_insights.is_recruiting_company,
        website=proxycurl_data.get("website"),
        industry=proxycurl_data.get("industry"),
        company_size_min=_safe_get_index(company_size, 0),
        company_size_max=_safe_get_index(company_size, 1),
        company_size_on_linkedin=proxycurl_data.get("company_size_on_linkedin"),
        hq_country=hq.get("country"),
        hq_city=hq.get("city"),
        hq_state=hq.get("state"),
        hq_postal_code=hq.get("postal_code"),
        company_type=proxycurl_data.get("company_type"),
        founded_year=proxycurl_data.get("founded_year"),
        tagline=proxycurl_data.get("tagline"),
        universal_name_id=proxycurl_data.get("universal_name_id"),
        profile_pic_url=proxycurl_data.get("profile_pic_url"),
        background_cover_image_url=proxycurl_data.get("background_cover_image_url"),
        specialities=_coerce_json_field(proxycurl_data.get("specialities")),
        locations=_coerce_json_field(proxycurl_data.get("locations")),
    )


def map_dataframe_row_to_job(
    row: pd.Series,
    company_id: int | None,
    structured_data: StructuredJobData | None = None,
) -> Job:
    city, state, country = parse_location_string(row.get("location"))
    job_types = _split_to_list(row.get("job_type"))
    emails = _split_to_list(row.get("emails"))

    job_kwargs = {
        "job_url": _safe_str(row.get("job_url")),
        "job_url_direct": _safe_str(row.get("job_url_direct")),
        "title": _safe_str(row.get("title")) or "Untitled Role",
        "company_name": _safe_str(row.get("company")),
        "company_id": company_id,
        "description": _safe_str(row.get("description")),
        "company_url": _safe_str(row.get("company_url")),
        "company_url_direct": _safe_str(row.get("company_url_direct")),
        "location_city": city,
        "location_state": state,
        "location_country": country,
        "compensation_min": _safe_float(row.get("min_amount")),
        "compensation_max": _safe_float(row.get("max_amount")),
        "compensation_currency": _safe_str(row.get("currency")),
        "compensation_interval": _safe_str(row.get("interval")),
        "job_type": job_types,
        "date_posted": _coerce_date(row.get("date_posted")),
        "is_remote": _safe_bool(row.get("is_remote")),
        "listing_type": _safe_str(row.get("listing_type")),
        "job_level": _safe_str(row.get("job_level")),
        "job_function": _safe_str(row.get("job_function")),
        "company_industry": _safe_str(row.get("company_industry")),
        "company_headquarters": _safe_str(row.get("company_headquarters")),
        "company_employees_count": _safe_str(row.get("company_employees_count")),
        "emails": emails,
    }

    # Add LLM-parsed fields if available
    if structured_data:
        job_kwargs.update({
            "required_skills": _coerce_json_field(structured_data.required_skills),
            "preferred_skills": _coerce_json_field(structured_data.preferred_skills),
            "required_years_experience": structured_data.required_years_experience,
            "required_education": structured_data.required_education,
            "preferred_education": structured_data.preferred_education,
            "responsibilities": _coerce_json_field(structured_data.responsibilities),
            "benefits": _coerce_json_field(structured_data.benefits),
            "work_arrangement": structured_data.work_arrangement,
            "team_size": structured_data.team_size,
            "technologies": _coerce_json_field(structured_data.technologies),
            "culture_keywords": _coerce_json_field(structured_data.culture_keywords),
            "summary": structured_data.summary,
            "job_categories": _coerce_json_field(structured_data.job_categories),
            "independent_contractor_friendly": structured_data.independent_contractor_friendly,
            "parsed_salary_currency": structured_data.salary_currency,
            "parsed_salary_min": structured_data.salary_min,
            "parsed_salary_max": structured_data.salary_max,
            "compensation_basis": structured_data.compensation_basis,
            "location_restrictions": _coerce_json_field(structured_data.location_restrictions),
            "exclusive_location_requirement": structured_data.exclusive_location_requirement,
        })

    return Job(**job_kwargs)


def parse_location_string(
    location_str: str | None,
) -> tuple[str | None, str | None, str | None]:
    if not location_str or not isinstance(location_str, str):
        return None, None, None

    parts = [segment.strip() for segment in location_str.split(",") if segment.strip()]
    city = parts[0] if len(parts) >= 1 else None
    state = parts[1] if len(parts) >= 2 else None
    country = parts[2] if len(parts) >= 3 else None
    return city, state, country


def normalize_linkedin_url(url: str | None) -> str | None:
    if not url:
        return None

    stripped = url.strip()
    if not stripped:
        return None

    if not stripped.startswith(("http://", "https://")):
        stripped = f"https://{stripped.lstrip('/')}"

    parsed = urlparse(stripped)
    netloc = parsed.netloc.lower()
    if "linkedin.com" not in netloc:
        return None

    path_parts = [segment for segment in parsed.path.split("/") if segment]
    if not path_parts or path_parts[0] != "company":
        return None

    company_slug = path_parts[1] if len(path_parts) > 1 else None
    if not company_slug:
        return None

    normalized_path = f"/company/{company_slug.strip('/')}/"

    return urlunparse(
        (
            "https",
            "www.linkedin.com",
            normalized_path,
            "",
            "",
            "",
        )
    )


def _coerce_json_field(value: Any) -> Any:
    if value in (None, "", [], {}):
        return None
    return value


def _safe_get_index(items: Iterable[Any], index: int) -> Any:
    if isinstance(items, (list, tuple)):
        try:
            return items[index]
        except IndexError:
            return None
    return None


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    try:
        if pd.isna(value):  # type: ignore[arg-type]
            return None
    except Exception:
        pass
    if isinstance(value, str):
        return value.strip() or None
    return str(value)


def _safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> bool | None:
    if value in (None, "", "None"):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"true", "yes", "1"}:
            return True
        if lowered in {"false", "no", "0"}:
            return False
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return None


def _coerce_date(value: Any) -> date | None:
    if value in (None, "", "None"):
        return None
    try:
        parsed = pd.to_datetime(value)
    except Exception:
        return None
    if pd.isna(parsed):
        return None
    return parsed.date()


def _split_to_list(value: Any) -> list[str] | None:
    if value in (None, "", "None"):
        return None
    if isinstance(value, list):
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        return cleaned or None
    if isinstance(value, str):
        parts = [part.strip() for part in value.split(",") if part.strip()]
        return parts or None
    return None
