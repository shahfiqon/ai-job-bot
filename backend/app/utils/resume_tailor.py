"""Utility functions for tailoring resume content using LangChain with Claude/OpenAI."""
import json
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from loguru import logger

from app.config import settings
from app.models.company import Company
from app.models.job import Job


def tailor_resume_for_job(
    resume_dict: dict[str, Any],
    job: Job,
    company: Company | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Tailor a user's resume JSON content for a specific job application.

    This function uses LangChain with Claude or OpenAI to intelligently refactor
    resume content (summaries, descriptions, highlights) while preserving the
    exact JSONResume schema structure.

    Args:
        resume_dict: User's resume as a Python dict (parsed from resume_json)
        job: Job model instance with job details and requirements
        company: Optional Company model instance with company information
        provider: Optional provider override ("claude" or "openai"), uses config default if None

    Returns:
        Tailored resume dict with same schema structure but optimized content.
        Returns original resume on any errors.

    Raises:
        ValueError: If resume_dict is invalid or required API keys are missing
    """
    if not resume_dict or not isinstance(resume_dict, dict):
        raise ValueError("resume_dict must be a non-empty dictionary")

    if not job:
        raise ValueError("job parameter is required")

    # Use provided provider or fall back to config
    llm_provider = provider or settings.RESUME_LLM_PROVIDER.lower()

    # Build comprehensive job context
    job_context = _build_job_context(job, company)

    try:
        # Get LLM instance
        llm = _get_llm_instance(llm_provider)

        # Create and run the tailoring chain
        chain = _create_tailoring_chain(llm)
        result = chain.invoke(
            {
                "resume_json": json.dumps(resume_dict, indent=2),
                "job_context": job_context,
            }
        )

        # Validate schema integrity
        tailored_resume = _validate_resume_schema(resume_dict, result)

        logger.info(
            f"Successfully tailored resume for job {job.id} using {llm_provider}"
        )
        return tailored_resume

    except Exception as exc:
        logger.exception(
            f"Error tailoring resume for job {job.id} with {llm_provider}: {exc}"
        )
        logger.warning("Returning original resume due to error")
        return _fallback_resume(resume_dict, str(exc))


def _get_llm_instance(provider: str):
    """
    Factory function to create LangChain LLM instance based on provider.

    Args:
        provider: "claude" or "openai"

    Returns:
        LangChain LLM instance (ChatAnthropic or ChatOpenAI)

    Raises:
        ValueError: If provider is invalid or API key is missing
    """
    provider = provider.lower()

    if provider == "claude":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is required for Claude provider. "
                "Set it in environment variables or .env file."
            )
        # Use configured model, defaulting to Claude model if still set to default
        model_name = settings.RESUME_LLM_MODEL
        return ChatAnthropic(
            model=model_name,
            temperature=settings.RESUME_LLM_TEMPERATURE,
            api_key=settings.ANTHROPIC_API_KEY,
        )

    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required for OpenAI provider. "
                "Set it in environment variables or .env file."
            )
        # Use configured model, but if it's the Claude default, use OpenAI default
        model_name = (
            "gpt-4o"
            if settings.RESUME_LLM_MODEL == "claude-3-5-sonnet-20241022"
            else settings.RESUME_LLM_MODEL
        )
        return ChatOpenAI(
            model=model_name,
            temperature=settings.RESUME_LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
        )

    else:
        raise ValueError(
            f"Invalid provider '{provider}'. Must be 'claude' or 'openai'"
        )


def _build_job_context(job: Job, company: Company | None = None) -> str:
    """
    Build comprehensive job context string from Job and Company models.

    Args:
        job: Job model instance
        company: Optional Company model instance

    Returns:
        Formatted context string with all relevant job and company information
    """
    context_parts = []

    # Job basic information
    context_parts.append("=== JOB INFORMATION ===")
    context_parts.append(f"Title: {job.title}")
    context_parts.append(f"Company: {job.company_name or 'N/A'}")
    if job.location_city or job.location_state or job.location_country:
        location_parts = [
            p
            for p in [job.location_city, job.location_state, job.location_country]
            if p
        ]
        context_parts.append(f"Location: {', '.join(location_parts)}")
    if job.job_type:
        context_parts.append(f"Job Type: {job.job_type}")
    if job.is_remote is not None:
        context_parts.append(f"Remote: {job.is_remote}")

    # Job description
    if job.description:
        context_parts.append(f"\nJob Description:\n{job.description}")

    # Structured job data (LLM-parsed fields)
    context_parts.append("\n=== JOB REQUIREMENTS ===")
    if job.required_skills:
        context_parts.append(f"Required Skills: {', '.join(job.required_skills)}")
    if job.preferred_skills:
        context_parts.append(f"Preferred Skills: {', '.join(job.preferred_skills)}")
    if job.required_years_experience:
        context_parts.append(
            f"Required Years of Experience: {job.required_years_experience}"
        )
    if job.required_education:
        context_parts.append(f"Required Education: {job.required_education}")
    if job.preferred_education:
        context_parts.append(f"Preferred Education: {job.preferred_education}")
    if job.technologies:
        context_parts.append(f"Technologies: {', '.join(job.technologies)}")
    if job.responsibilities:
        context_parts.append(
            f"Responsibilities:\n- " + "\n- ".join(job.responsibilities)
        )
    if job.work_arrangement:
        context_parts.append(f"Work Arrangement: {job.work_arrangement}")
    if job.job_categories:
        context_parts.append(f"Job Categories: {', '.join(job.job_categories)}")
    if job.culture_keywords:
        context_parts.append(f"Culture Keywords: {', '.join(job.culture_keywords)}")
    if job.benefits:
        context_parts.append(f"Benefits: {', '.join(job.benefits)}")

    # Company information
    if company:
        context_parts.append("\n=== COMPANY INFORMATION ===")
        context_parts.append(f"Company Name: {company.name}")
        if company.description:
            context_parts.append(f"Description: {company.description}")
        if company.industry:
            context_parts.append(f"Industry: {company.industry}")
        if company.tagline:
            context_parts.append(f"Tagline: {company.tagline}")
        if company.company_type:
            context_parts.append(f"Company Type: {company.company_type}")
        if company.founded_year:
            context_parts.append(f"Founded: {company.founded_year}")
        if company.specialities:
            context_parts.append(
                f"Specialties: {', '.join(company.specialities) if isinstance(company.specialities, list) else str(company.specialities)}"
            )

    return "\n".join(context_parts)


def _create_tailoring_chain(llm):
    """
    Create LangChain chain for resume tailoring.

    Chain structure: PromptTemplate → LLM → JsonOutputParser

    Args:
        llm: LangChain LLM instance

    Returns:
        LangChain chain ready to invoke
    """

    # Prompt Example 
    """
    You are an expert Resume Writer and ATS Optimization Specialist.
JOB DESCRIPTION:
{job_description}
MY MASTER RESUME:
{resume_text}
TASK:
Rewrite my resume to perfectly match the Job Description.
RULES:
1. Use the EXACT keywords from the JD in skills and summary sections.
2. Rephrase bullet points to match the responsibilities and metrics they care about.
3. Do NOT lie or invent new experience.
4. Only use real experience from my resume.
5. Output in clean, well-formatted MARKDOWN.
"""

    system_prompt = """You are an expert resume tailoring assistant. Your task is to intelligently refactor a user's resume content to better match a specific job application while STRICTLY preserving the exact JSON schema structure.

CRITICAL RULES:
1. You MUST return a JSON object with the EXACT same structure as the input resume
2. All top-level keys must be preserved (basics, work, education, skills, etc.)
3. All nested object structures must be maintained
4. Array fields must be present (you can modify array length for highlights/descriptions, but preserve other arrays)
5. DO NOT add new keys or remove existing keys
6. DO NOT change data types (strings stay strings, arrays stay arrays, objects stay objects)

TAILORING INSTRUCTIONS:
- Optimize the professional summary (basics.summary) to highlight relevant experience for this job
- Refine work experience summaries and highlights to emphasize relevant achievements and skills
- Reorder skills to prioritize those mentioned in the job requirements
- Adjust work experience descriptions to use keywords from the job description
- Maintain authenticity - only enhance existing content, don't fabricate experiences
- Keep all factual information accurate (dates, company names, locations, etc.)

Your output must be valid JSON that can be parsed directly. Return ONLY the JSON object, no additional text or explanations."""

    user_prompt_template = """Job Context:
{job_context}

Original Resume (JSON):
{resume_json}

Please tailor this resume for the job above. Return the tailored resume as a JSON object with the EXACT same structure as the input, but with optimized content."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt_template),
        ]
    )

    # Create chain: prompt → LLM → JSON parser
    parser = JsonOutputParser()
    chain = prompt | llm | parser

    return chain


def _validate_resume_schema(
    original_resume: dict[str, Any], tailored_resume: dict[str, Any]
) -> dict[str, Any]:
    """
    Validate that tailored resume maintains the same schema structure as original.

    Args:
        original_resume: Original resume dict
        tailored_resume: LLM-generated tailored resume dict

    Returns:
        Validated and potentially corrected resume dict

    Raises:
        ValueError: If schema validation fails critically
    """
    if not isinstance(tailored_resume, dict):
        logger.error("Tailored resume is not a dictionary")
        raise ValueError("LLM returned invalid output: not a dictionary")

    # Check top-level keys
    original_keys = set(original_resume.keys())
    tailored_keys = set(tailored_resume.keys())

    missing_keys = original_keys - tailored_keys
    extra_keys = tailored_keys - original_keys

    if missing_keys:
        logger.warning(f"Missing keys in tailored resume: {missing_keys}")
        # Restore missing keys from original
        for key in missing_keys:
            tailored_resume[key] = original_resume[key]

    if extra_keys:
        logger.warning(f"Extra keys in tailored resume: {extra_keys}")
        # Remove extra keys
        for key in extra_keys:
            del tailored_resume[key]

    # Validate critical JSONResume sections exist
    critical_sections = ["basics"]
    for section in critical_sections:
        if section not in tailored_resume:
            logger.error(f"Critical section '{section}' missing from tailored resume")
            tailored_resume[section] = original_resume.get(section, {})

    # Ensure basics is a dict
    if not isinstance(tailored_resume.get("basics"), dict):
        logger.warning("basics section is not a dict, restoring from original")
        tailored_resume["basics"] = original_resume.get("basics", {})

    return tailored_resume


def _fallback_resume(resume_dict: dict[str, Any], error_message: str) -> dict[str, Any]:
    """
    Return original resume with error logging.

    Args:
        resume_dict: Original resume dict
        error_message: Error message for logging

    Returns:
        Original resume dict unchanged
    """
    logger.error(f"Resume tailoring failed: {error_message}")
    logger.info("Returning original resume as fallback")
    return resume_dict

