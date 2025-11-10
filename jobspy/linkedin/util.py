from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

from jobspy.model import JobType, Location
from jobspy.util import get_enum_from_job_type


def job_type_code(job_type_enum: JobType) -> str:
    return {
        JobType.FULL_TIME: "F",
        JobType.PART_TIME: "P",
        JobType.INTERNSHIP: "I",
        JobType.CONTRACT: "C",
        JobType.TEMPORARY: "T",
    }.get(job_type_enum, "")


def parse_job_type(soup_job_type: BeautifulSoup) -> list[JobType] | None:
    """
    Gets the job type from job page
    :param soup_job_type:
    :return: JobType
    """
    h3_tag = soup_job_type.find(
        "h3",
        class_="description__job-criteria-subheader",
        string=lambda text: "Employment type" in text,
    )
    employment_type = None
    if h3_tag:
        employment_type_span = h3_tag.find_next_sibling(
            "span",
            class_="description__job-criteria-text description__job-criteria-text--criteria",
        )
        if employment_type_span:
            employment_type = employment_type_span.get_text(strip=True)
            employment_type = employment_type.lower()
            employment_type = employment_type.replace("-", "")

    return [get_enum_from_job_type(employment_type)] if employment_type else []


def parse_job_level(soup_job_level: BeautifulSoup) -> str | None:
    """
    Gets the job level from job page
    :param soup_job_level:
    :return: str
    """
    h3_tag = soup_job_level.find(
        "h3",
        class_="description__job-criteria-subheader",
        string=lambda text: "Seniority level" in text,
    )
    job_level = None
    if h3_tag:
        job_level_span = h3_tag.find_next_sibling(
            "span",
            class_="description__job-criteria-text description__job-criteria-text--criteria",
        )
        if job_level_span:
            job_level = job_level_span.get_text(strip=True)

    return job_level


def parse_company_industry(soup_industry: BeautifulSoup) -> str | None:
    """
    Gets the company industry from job page
    :param soup_industry:
    :return: str
    """
    h3_tag = soup_industry.find(
        "h3",
        class_="description__job-criteria-subheader",
        string=lambda text: "Industries" in text,
    )
    industry = None
    if h3_tag:
        industry_span = h3_tag.find_next_sibling(
            "span",
            class_="description__job-criteria-text description__job-criteria-text--criteria",
        )
        if industry_span:
            industry = industry_span.get_text(strip=True)

    return industry


def parse_company_headquarters(soup_headquarters: BeautifulSoup) -> str | None:
    """
    Gets the company headquarters from job page
    :param soup_headquarters:
    :return: str
    """
    h3_tag = soup_headquarters.find(
        "h3",
        class_="description__job-criteria-subheader",
        string=lambda text: "Headquarters" in text,
    )
    headquarters = None
    if h3_tag:
        headquarters_span = h3_tag.find_next_sibling(
            "span",
            class_="description__job-criteria-text description__job-criteria-text--criteria",
        )
        if headquarters_span:
            headquarters = headquarters_span.get_text(strip=True)

    return headquarters


def parse_company_employees_count(soup_employees_count: BeautifulSoup) -> str | None:
    """
    Gets the company employees count from job page
    :param soup_employees_count:
    :return: str
    """
    h3_tag = soup_employees_count.find(
        "h3",
        class_="description__job-criteria-subheader",
        string=lambda text: "Company size" in text,
    )
    employees_count = None
    if h3_tag:
        employees_count_span = h3_tag.find_next_sibling(
            "span",
            class_="description__job-criteria-text description__job-criteria-text--criteria",
        )
        if employees_count_span:
            employees_count = employees_count_span.get_text(strip=True)

    return employees_count


def parse_job_poster(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """
    Gets the job poster name and profile URL from the hiring team section
    :param soup: BeautifulSoup object of the job page
    :return: tuple of (name, profile_url) where each is str | None
    """
    try:
        # Search for heading containing "hiring team" (case-insensitive)
        heading = soup.find(
            ["h2", "h3"],
            string=lambda text: text and "hiring team" in text.lower()
        )

        if not heading:
            return (None, None)

        # Find the nearest section container
        section_container = heading.find_parent(["section", "div", "ul"])
        if not section_container:
            return (None, None)

        # Find the first profile anchor whose href contains /in/
        profile_anchor = section_container.find(
            "a",
            href=lambda href: href and "/in/" in href
        )

        if not profile_anchor:
            return (None, None)

        # Extract the display name from the anchor text or a sibling element
        name = profile_anchor.get_text(strip=True)
        if not name:
            # Try to find name in sibling elements
            name_element = profile_anchor.find_next_sibling()
            if name_element:
                name = name_element.get_text(strip=True)

        # Get the href and normalize the URL
        href = profile_anchor.get("href", "")
        if not href:
            return (name or None, None)

        # Parse URL and remove query parameters
        parsed = urlparse(href)
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            "",  # params
            "",  # query
            ""   # fragment
        ))

        # Make absolute URL if relative
        if not clean_url.startswith("http"):
            clean_url = f"https://www.linkedin.com{clean_url if clean_url.startswith('/') else '/' + clean_url}"

        return (name or None, clean_url)

    except Exception:
        return (None, None)


def is_job_remote(title: dict, description: str, location: Location) -> bool:
    """
    Searches the title, location, and description to check if job is remote
    """
    remote_keywords = ["remote", "work from home", "wfh"]
    location = location.display_location()
    full_string = f'{title} {description} {location}'.lower()
    is_remote = any(keyword in full_string for keyword in remote_keywords)
    return is_remote
