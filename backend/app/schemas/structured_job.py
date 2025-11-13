"""Pydantic schema for structured job data extracted by LLM."""
from pydantic import BaseModel, Field


class StructuredJobData(BaseModel):
    """
    Structured job data extracted from a job description using LLM parsing.
    
    This model represents the key information extracted from a job posting,
    including skills, requirements, responsibilities, and benefits.
    """
    
    required_skills: list[str] = Field(
        default_factory=list,
        description="List of required technical and professional skills",
    )
    preferred_skills: list[str] = Field(
        default_factory=list,
        description="List of preferred/nice-to-have skills",
    )
    required_years_experience: int | None = Field(
        default=None,
        description="Minimum years of experience required",
    )
    required_education: str | None = Field(
        default=None,
        description="Required education level (e.g., 'Bachelor's degree', 'Master's degree')",
    )
    preferred_education: str | None = Field(
        default=None,
        description="Preferred education level",
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="List of key job responsibilities and duties",
    )
    benefits: list[str] = Field(
        default_factory=list,
        description="List of benefits, perks, and compensation details",
    )
    work_arrangement: str | None = Field(
        default=None,
        description="Work arrangement (e.g., 'Remote', 'Hybrid', 'On-site')",
    )
    team_size: str | None = Field(
        default=None,
        description="Team size or structure if mentioned",
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="List of specific technologies, frameworks, or tools",
    )
    culture_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords indicating company culture (e.g., 'collaborative', 'fast-paced')",
    )
    summary: str | None = Field(
        default=None,
        description="Brief 2-3 sentence summary of the role",
    )
    job_categories: list[str] = Field(
        default_factory=list,
        description=(
            "List of normalized job labels (e.g., 'AI/ML', 'Blockchain/Crypto', "
            "'Data Engineering', 'Full Stack', 'Frontend', 'Backend', 'DevOps/SRE', "
            "'Mobile', 'Product/Design') that match the posting"
        ),
    )
    independent_contractor_friendly: bool | None = Field(
        default=None,
        description=(
            "True if the posting explicitly allows 1099 or independent contractors, "
            "False if it explicitly disallows them, otherwise null"
        ),
    )
    salary_currency: str | None = Field(
        default=None,
        description="ISO currency code for any stated salary or hourly rate (e.g., 'USD', 'EUR')",
    )
    salary_min: float | None = Field(
        default=None,
        description="Lower bound of the stated salary or rate converted to a pure number",
    )
    salary_max: float | None = Field(
        default=None,
        description="Upper bound of the stated salary or rate converted to a pure number",
    )
    compensation_basis: str | None = Field(
        default=None,
        description="Compensation cadence if specified (e.g., 'Hourly', 'Annual', 'Monthly', 'Contract')",
    )
    location_restrictions: list[str] = Field(
        default_factory=list,
        description="Regions or countries explicitly required or excluded by the posting",
    )
    exclusive_location_requirement: bool | None = Field(
        default=None,
        description="True if the job states applicants must live in specific areas and others are not accepted",
    )
