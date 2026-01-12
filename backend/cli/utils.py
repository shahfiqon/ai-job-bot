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
                f"Proxycurl HTTP error ({status_code}) while enriching {linkedin_url}: {exc}",
            )
            return None
        except requests.RequestException as exc:
            logger.error(f"Proxycurl request failure for {linkedin_url}: {exc}")
            return None

    return None


def map_proxycurl_to_company(
    proxycurl_data: dict[str, Any],
    linkedin_url: str,
) -> Company:
    company_size = proxycurl_data.get("company_size") or []
    hq = proxycurl_data.get("hq") or {}
    description = proxycurl_data.get("description")
    # description_insights = parse_company_description(description)

    return Company(
        linkedin_url=linkedin_url,
        linkedin_internal_id=proxycurl_data.get("linkedin_internal_id"),
        name=proxycurl_data.get("name") or "Unknown",
        description=description,
        has_own_products=False, # deprecated 
        is_recruiting_company=False, # deprecated
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
    structured_data: dict | None = None,
) -> Job:
    city, state, country = parse_location_string(row.get("location"))
    job_types = _split_to_list(row.get("job_type"))
    emails = _split_to_list(row.get("emails"))

    # Safely get date_posted and applicants_count, handling missing columns and NaN values
    date_posted_value = None
    if "date_posted" in row.index:
        date_posted_value = row["date_posted"]
        if pd.isna(date_posted_value):
            date_posted_value = None
        else:
            logger.debug(f"Found date_posted value: {date_posted_value} (type: {type(date_posted_value)})")
    else:
        logger.debug("date_posted column not found in row")
    
    applicants_count_value = None
    if "applicants_count" in row.index:
        applicants_count_value = row["applicants_count"]
        if pd.isna(applicants_count_value):
            applicants_count_value = None
        else:
            logger.debug(f"Found applicants_count value: {applicants_count_value} (type: {type(applicants_count_value)})")
    else:
        logger.debug("applicants_count column not found in row")

    job_kwargs = {
        "job_url": _safe_str(row.get("job_url")),
        "job_url_direct": _safe_str(row.get("job_url_direct")),
        "title": _safe_str(row.get("title")) or "Untitled Role",
        "company_name": _truncate_str(_safe_str(row.get("company")), 512),
        "company_id": company_id,
        "description": _safe_str(row.get("description")),
        "company_url": _safe_str(row.get("company_url")),
        "company_url_direct": _safe_str(row.get("company_url_direct")),
        "location_city": _truncate_str(city, 512),
        "location_state": _truncate_str(state, 512),
        "location_country": _truncate_str(country, 512),
        "compensation_min": _safe_float(row.get("min_amount")),
        "compensation_max": _safe_float(row.get("max_amount")),
        "compensation_currency": _safe_str(row.get("currency")),
        "compensation_interval": _safe_str(row.get("interval")),
        "job_type": job_types,
        "date_posted": _coerce_date(date_posted_value),
        "is_remote": _safe_bool(row.get("is_remote")),
        "listing_type": _safe_str(row.get("listing_type")),
        "job_level": _safe_str(row.get("job_level")),
        "job_function": _safe_str(row.get("job_function")),
        "company_industry": _truncate_str(_safe_str(row.get("company_industry")), 512),
        "company_headquarters": _truncate_str(_safe_str(row.get("company_headquarters")), 512),
        "company_employees_count": _safe_str(row.get("company_employees_count")),
        "applicants_count": _safe_int(applicants_count_value),
        "emails": emails,
    }

    # Add DSPy-parsed fields if available
    if structured_data:
        # Map overlapping fields (required_skills, preferred_skills, required_years_experience, responsibilities)
        if "required_skills" in structured_data:
            job_kwargs["required_skills"] = _coerce_json_field(structured_data["required_skills"])
        if "preferred_skills" in structured_data:
            job_kwargs["preferred_skills"] = _coerce_json_field(structured_data["preferred_skills"])
        if "required_years_experience" in structured_data:
            job_kwargs["required_years_experience"] = structured_data["required_years_experience"]
        if "responsibilities" in structured_data:
            job_kwargs["responsibilities"] = _coerce_json_field(structured_data["responsibilities"])
        
        # Map new DSPy-specific fields
        if "is_python_main" in structured_data:
            job_kwargs["is_python_main"] = structured_data["is_python_main"]
        if "contract_feasible" in structured_data:
            job_kwargs["contract_feasible"] = structured_data["contract_feasible"]
        if "relocate_required" in structured_data:
            job_kwargs["relocate_required"] = structured_data["relocate_required"]
        if "specific_locations" in structured_data:
            job_kwargs["specific_locations"] = _coerce_json_field(structured_data["specific_locations"])
        if "accepts_non_us" in structured_data:
            job_kwargs["accepts_non_us"] = structured_data["accepts_non_us"]
        if "screening_required" in structured_data:
            job_kwargs["screening_required"] = structured_data["screening_required"]
        if "company_size" in structured_data:
            job_kwargs["company_size"] = _truncate_str(structured_data["company_size"], 64) if structured_data["company_size"] else None

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
    if not url or not isinstance(url, str):
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


def _truncate_str(value: str | None, max_length: int) -> str | None:
    """Truncate a string to a maximum length, returning None if value is None."""
    if value is None:
        return None
    if len(value) <= max_length:
        return value
    return value[:max_length]


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


def _safe_int(value: Any) -> int | None:
    if value in (None, "", "None"):
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_date(value: Any) -> date | None:
    if value in (None, "", "None"):
        return None
    try:
        # Check for NaN/NaT before attempting conversion
        if pd.isna(value):
            return None
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
