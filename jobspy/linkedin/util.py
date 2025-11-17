from datetime import date, datetime, timedelta
import re

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


def parse_applicants_count(soup: BeautifulSoup) -> int | None:
    """
    Gets the number of applicants from job detail page
    :param soup: BeautifulSoup object of the job page
    :return: integer count of applicants or None
    """
    try:
        # Pattern to match "X applicants", "Over X applicants", "X+ applicants", etc.
        applicant_patterns = [
            re.compile(r"(\d+)\s*applicants?", re.IGNORECASE),
            re.compile(r"over\s+(\d+)\s*applicants?", re.IGNORECASE),
            re.compile(r"(\d+)\+\s*applicants?", re.IGNORECASE),
            re.compile(r"(\d+)\s*people?\s+applied", re.IGNORECASE),
        ]

        # Search for elements containing "applicant" text
        search_elements = soup.find_all(
            ["span", "div", "p", "strong", "b"],
            string=lambda text: text and re.search(r"applicant", text, re.IGNORECASE)
        )

        for element in search_elements:
            text = element.get_text(strip=True)
            for pattern in applicant_patterns:
                match = pattern.search(text)
                if match:
                    try:
                        count = int(match.group(1))
                        return count
                    except (ValueError, IndexError):
                        continue

        # Also search in parent elements that might contain the applicant info
        # Look for common LinkedIn classes that might contain applicant info
        applicant_classes = [
            "num-applicants",
            "applicants-count",
            "job-details-jobs-unified-top-card__applicant-count",
            "jobs-unified-top-card__applicant-count",
        ]

        for class_name in applicant_classes:
            applicant_elem = soup.find(class_=lambda x: x and class_name in str(x).lower())
            if applicant_elem:
                text = applicant_elem.get_text(strip=True)
                for pattern in applicant_patterns:
                    match = pattern.search(text)
                    if match:
                        try:
                            count = int(match.group(1))
                            return count
                        except (ValueError, IndexError):
                            continue

        # Search more broadly in the top section of the job page
        # LinkedIn often shows applicant count near the top
        top_section = soup.find(["header", "section", "div"], class_=lambda x: x and ("top-card" in str(x).lower() or "job-header" in str(x).lower()))
        if top_section:
            text = top_section.get_text()
            for pattern in applicant_patterns:
                match = pattern.search(text)
                if match:
                    try:
                        count = int(match.group(1))
                        return count
                    except (ValueError, IndexError):
                        continue

    except Exception:
        pass

    return None


def parse_date_posted(soup: BeautifulSoup) -> date | None:
    """
    Gets the job posted date from job detail page
    :param soup: BeautifulSoup object of the job page
    :return: date object or None
    """
    try:
        # First, try to find the specific LinkedIn class for posted date
        # The class can be: "posted-time-ago__text posted-time-ago__text--new topcard__flavor--metadata"
        posted_time_classes = [
            "posted-time-ago__text",
            "topcard__flavor--metadata",
        ]
        
        # Look for elements with these classes (can be in class list)
        # Also check for <time> elements which often have datetime attributes
        date_elem = soup.find("time", class_=lambda x: x and any(cls in str(x) for cls in posted_time_classes))
        if not date_elem:
            # Try finding by any of the classes
            for class_name in posted_time_classes:
                date_elem = soup.find(class_=lambda x: x and class_name in str(x))
                if date_elem:
                    break
        
        if date_elem:
            text = date_elem.get_text(strip=True)
            # Try to parse relative time like "2 days ago", "1 week ago", etc.
            posted_patterns = [
                re.compile(r"(\d+)\s+(day|days|week|weeks|month|months|hour|hours)\s+ago", re.IGNORECASE),
                re.compile(r"posted\s+(\d+)\s+(day|days|week|weeks|month|months|hour|hours)\s+ago", re.IGNORECASE),
                re.compile(r"reposted\s+(\d+)\s+(day|days|week|weeks|month|months|hour|hours)\s+ago", re.IGNORECASE),
            ]
            for pattern in posted_patterns:
                match = pattern.search(text.lower())
                if match:
                    amount = int(match.group(1))
                    unit = match.group(2).lower()
                    today = date.today()
                    if "hour" in unit:
                        return today
                    elif "day" in unit:
                        return today - timedelta(days=amount)
                    elif "week" in unit:
                        return today - timedelta(weeks=amount)
                    elif "month" in unit:
                        return today - timedelta(days=amount * 30)
            # If we found the element but couldn't parse, try to look for datetime attribute
            if date_elem.get("datetime"):
                try:
                    datetime_str = date_elem["datetime"]
                    dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
                    return dt.date()
                except (ValueError, AttributeError):
                    try:
                        return datetime.strptime(datetime_str, "%Y-%m-%d").date()
                    except (ValueError, AttributeError):
                        pass

        # Look for spans or divs containing "Posted" or "Reposted" text
        posted_patterns = [
            re.compile(r"posted\s+(\d+)\s+(day|days|week|weeks|month|months|hour|hours)\s+ago", re.IGNORECASE),
            re.compile(r"reposted\s+(\d+)\s+(day|days|week|weeks|month|months|hour|hours)\s+ago", re.IGNORECASE),
        ]

        # Search in common LinkedIn job page sections for elements containing "Posted" or "Reposted"
        search_elements = soup.find_all(["span", "div", "p"], string=lambda text: text and re.search(r"(posted|reposted)", text, re.IGNORECASE))
        
        for element in search_elements:
            text = element.get_text(strip=True).lower()
            for pattern in posted_patterns:
                match = pattern.search(text)
                if match:
                    amount = int(match.group(1))
                    unit = match.group(2).lower()
                    
                    # Calculate the date based on the relative time
                    today = date.today()
                    if "hour" in unit:
                        # For hours, we'll use today's date (too granular for date field)
                        return today
                    elif "day" in unit:
                        return today - timedelta(days=amount)
                    elif "week" in unit:
                        return today - timedelta(weeks=amount)
                    elif "month" in unit:
                        # Approximate months as 30 days
                        return today - timedelta(days=amount * 30)

        # Look for text containing date patterns like "Posted on [date]"
        date_pattern = re.compile(r"(posted|reposted)\s+(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", re.IGNORECASE)
        # Search more broadly for date patterns
        all_text_elements = soup.find_all(["span", "div", "p"])
        for element in all_text_elements:
            text = element.get_text(strip=True)
            match = date_pattern.search(text)
            if match:
                date_str = match.group(2)
                # Try common date formats
                for fmt in ["%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue

        # Look for elements with classes that might contain date info
        date_classes = [
            "posted-date",
            "job-posted-date",
            "posted-time",
            "t-black--light",
        ]
        for class_name in date_classes:
            date_elem = soup.find(class_=lambda x: x and class_name in str(x).lower())
            if date_elem:
                text = date_elem.get_text(strip=True)
                # Try to extract date from text
                for pattern in posted_patterns:
                    match = pattern.search(text.lower())
                    if match:
                        amount = int(match.group(1))
                        unit = match.group(2).lower()
                        today = date.today()
                        if "day" in unit:
                            return today - timedelta(days=amount)
                        elif "week" in unit:
                            return today - timedelta(weeks=amount)
                        elif "month" in unit:
                            return today - timedelta(days=amount * 30)

    except Exception:
        pass

    return None


def is_job_remote(title: dict, description: str, location: Location) -> bool:
    """
    Searches the title, location, and description to check if job is remote
    """
    remote_keywords = ["remote", "work from home", "wfh"]
    location = location.display_location()
    full_string = f'{title} {description} {location}'.lower()
    is_remote = any(keyword in full_string for keyword in remote_keywords)
    return is_remote
