"""
Job Description Parser - Extract structured information from job descriptions.

This script uses the DSPy framework to analyze job postings and extract:
- Python-centric roles
- Fully remote positions
- Startup/small company opportunities
- 1099/freelance/contract arrangements
- Roles without clearance/fingerprinting/credit checks
- Required and preferred skills
- Required years of experience
- Key responsibilities

Requirements:
    pip install dspy-ai requests

Quick Start:
    # Start llama.cpp server with OpenAI-compatible endpoint on http://localhost:8080/v1
    python job_parser.py job_description.txt

Usage Examples:
    # Basic usage (outputs job_description.json)
    python job_parser.py job.txt

    # Process all files in a directory
    python job_parser.py /path/to/job_descriptions/

    # Custom output location
    python job_parser.py job.txt --output ~/analysis/tech_role.json

    # Custom llama.cpp endpoint
    python job_parser.py job.txt --endpoint http://192.168.1.100:8080/v1

    # Verbose mode for debugging
    python job_parser.py job.txt -v

    # Process directory with verbose output
    python job_parser.py /path/to/jobs/ -v

    # Combined flags
    python job_parser.py job.txt -o result.json --endpoint http://localhost:8000/v1 -v
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional

import dspy
from dspy.clients.lm import OpenAIProvider
from pydantic import BaseModel, Field


# Configuration constants
DEFAULT_ENDPOINT = "http://localhost:8080/v1"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 500
MIN_WORDS_WARNING = 50
CONTEXT_WINDOW_WARNING = 4000  # Approximate token limit warning threshold
SUPPORTED_EXTENSIONS = {".txt", ".md", ".text"}  # File extensions to process from directories


# Pydantic models for output schema
class FieldValue(BaseModel):
    """Value with confidence score for a single field."""
    value: Optional[bool | str | int | list[str]] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class JobExtractionOutput(BaseModel):
    """Complete extraction output schema."""
    is_python_main: FieldValue
    is_remote_in_usa: FieldValue
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

    is_remote_in_usa: bool = dspy.OutputField(
        desc="True ONLY if: (1) the job is fully remote/work-from-home AND (2) it mentions 'USA' or 'United States' WITHOUT requiring a specific city or state. False if: job requires specific location (city/state like 'Austin, TX' or 'California'), requires on-site, hybrid with mandatory office days, or is not remote. A job that says 'Remote' but requires 'Austin, TX' should be False because it's location-specific, not truly remote within USA."
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


async def extract_job_info(job_description: str, endpoint: str, verbose: bool = False) -> dict:
    """
    Extract structured information from job description using DSPy (async).

    Args:
        job_description: Full text of the job description
        endpoint: OpenAI-compatible API endpoint URL
        verbose: Enable verbose logging

    Returns:
        Dictionary with extracted fields and confidence scores
    """
    start_time = time.time()

    # Configure DSPy with OpenAI-compatible endpoint
    if verbose:
        print(f"[DEBUG] Configuring DSPy with endpoint: {endpoint}", file=sys.stderr)

    lm = dspy.LM(
        model="openai/default",  # llama.cpp uses "default" or model name
        api_base=endpoint,
        model_type="chat",
        api_key="not-needed",  # llama.cpp doesn't require auth
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    dspy.configure(lm=lm)

    # Create prediction instance and wrap with asyncify for async execution
    extractor = dspy.Predict(JobExtraction)
    async_extractor = dspy.asyncify(extractor)

    if verbose:
        print(f"[DEBUG] Calling DSPy Predict (async) with job description ({len(job_description)} chars)", file=sys.stderr)

    # Execute extraction asynchronously
    try:
        result = await async_extractor(job_description=job_description)
    except Exception as e:
        print(f"Error during LLM extraction: {e}", file=sys.stderr)
        raise

    processing_time = time.time() - start_time

    if verbose:
        print(f"[DEBUG] Extraction completed in {processing_time:.2f}s", file=sys.stderr)
        print(f"[DEBUG] Raw result: {result}", file=sys.stderr)

    # Parse specific_locations string into array
    specific_locations_str = getattr(result, "specific_locations", "")
    specific_locations_list = []
    if specific_locations_str and specific_locations_str.strip():
        # Split by comma and clean up whitespace
        specific_locations_list = [
            loc.strip() for loc in specific_locations_str.split(",") if loc.strip()
        ]

    # Extract values and compute confidence scores
    # Note: DSPy doesn't provide native confidence scores, so we use heuristics
    def compute_confidence(value, field_name: str) -> float:
        """Heuristic confidence scoring based on value type and field."""
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

    # Build output structure
    output = {
        "is_python_main": FieldValue(
            value=getattr(result, "is_python_main", None),
            confidence=compute_confidence(getattr(result, "is_python_main", None), "is_python_main")
        ),
        "is_remote_in_usa": FieldValue(
            value=getattr(result, "is_remote_in_usa", None),
            confidence=compute_confidence(getattr(result, "is_remote_in_usa", None), "is_remote_in_usa")
        ),
        "contract_feasible": FieldValue(
            value=getattr(result, "contract_feasible", None),
            confidence=compute_confidence(getattr(result, "contract_feasible", None), "contract_feasible")
        ),
        "relocate_required": FieldValue(
            value=getattr(result, "relocate_required", None),
            confidence=compute_confidence(getattr(result, "relocate_required", None), "relocate_required")
        ),
        "specific_locations": FieldValue(
            value=specific_locations_list,
            confidence=compute_confidence(specific_locations_list, "specific_locations")
        ),
        "accepts_non_us": FieldValue(
            value=getattr(result, "accepts_non_us", None),
            confidence=compute_confidence(getattr(result, "accepts_non_us", None), "accepts_non_us")
        ),
        "screening_required": FieldValue(
            value=getattr(result, "screening_required", None),
            confidence=compute_confidence(getattr(result, "screening_required", None), "screening_required")
        ),
        "company_size": FieldValue(
            value=getattr(result, "company_size", "unknown"),
            confidence=compute_confidence(getattr(result, "company_size", "unknown"), "company_size")
        ),
        "required_skills": FieldValue(
            value=getattr(result, "required_skills", []),
            confidence=compute_confidence(getattr(result, "required_skills", []), "required_skills")
        ),
        "preferred_skills": FieldValue(
            value=getattr(result, "preferred_skills", []),
            confidence=compute_confidence(getattr(result, "preferred_skills", []), "preferred_skills")
        ),
        "required_years_experience": FieldValue(
            value=getattr(result, "required_years_experience", None),
            confidence=compute_confidence(getattr(result, "required_years_experience", None), "required_years_experience")
        ),
        "responsibilities": FieldValue(
            value=getattr(result, "responsibilities", []),
            confidence=compute_confidence(getattr(result, "responsibilities", []), "responsibilities")
        ),
        "metadata": {
            "processing_time_seconds": round(processing_time, 2)
        }
    }

    if verbose:
        print(f"[DEBUG] Extracted fields:", file=sys.stderr)
        for key, field_value in output.items():
            if key != "metadata":
                print(f"  {key}: {field_value.value} (confidence: {field_value.confidence})", file=sys.stderr)

    return output


def read_job_description(file_path: Path, verbose: bool = False) -> str:
    """
    Read job description from file with validation and truncation.

    Args:
        file_path: Path to input text file
        verbose: Enable verbose logging

    Returns:
        Job description text (possibly truncated)
    """
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    content = file_path.read_text(encoding="utf-8")

    if len(content.strip()) == 0:
        print("Warning: Input file is empty", file=sys.stderr)

    # Check word count
    word_count = len(content.split())
    if word_count < MIN_WORDS_WARNING:
        print(f"Warning: Input is very short ({word_count} words, minimum {MIN_WORDS_WARNING} recommended)", file=sys.stderr)

    # Approximate token count (rough estimate: 1 token ≈ 4 characters)
    approx_tokens = len(content) // 4
    if approx_tokens > CONTEXT_WINDOW_WARNING:
        print(f"Warning: Input may exceed context window (~{approx_tokens} tokens, limit ~{CONTEXT_WINDOW_WARNING})", file=sys.stderr)
        print(f"Warning: Truncating to ~{CONTEXT_WINDOW_WARNING * 4} characters", file=sys.stderr)
        # Truncate to approximate token limit
        content = content[:CONTEXT_WINDOW_WARNING * 4]

    if verbose:
        print(f"[DEBUG] Read {len(content)} characters from {file_path}", file=sys.stderr)

    return content


async def process_single_file(input_path: Path, output_path: Optional[Path], endpoint: str, verbose: bool) -> dict:
    """
    Process a single job description file (async).

    Args:
        input_path: Path to input file
        output_path: Optional output path (auto-generated if None)
        endpoint: LLM endpoint URL
        verbose: Enable verbose logging

    Returns:
        Dictionary with extraction results
    """
    # Determine output path
    if output_path is None:
        # Auto-generate from input filename
        output_path = input_path.with_suffix(".json")

    if verbose:
        print(f"[DEBUG] Processing: {input_path}", file=sys.stderr)
        print(f"[DEBUG] Output file: {output_path}", file=sys.stderr)

    # Read job description
    try:
        job_description = read_job_description(input_path, verbose=verbose)
    except Exception as e:
        print(f"Error reading input file {input_path}: {e}", file=sys.stderr)
        return None

    # Extract information asynchronously
    try:
        extraction_result = await extract_job_info(
            job_description=job_description,
            endpoint=endpoint,
            verbose=verbose
        )
    except Exception as e:
        print(f"Error during extraction for {input_path}: {e}", file=sys.stderr)
        return None

    # Convert to JSON-serializable format
    output_dict = {
        "is_python_main": {
            "value": extraction_result["is_python_main"].value,
            "confidence": extraction_result["is_python_main"].confidence
        },
        "is_remote_in_usa": {
            "value": extraction_result["is_remote_in_usa"].value,
            "confidence": extraction_result["is_remote_in_usa"].confidence
        },
        "contract_feasible": {
            "value": extraction_result["contract_feasible"].value,
            "confidence": extraction_result["contract_feasible"].confidence
        },
        "relocate_required": {
            "value": extraction_result["relocate_required"].value,
            "confidence": extraction_result["relocate_required"].confidence
        },
        "specific_locations": {
            "value": extraction_result["specific_locations"].value,
            "confidence": extraction_result["specific_locations"].confidence
        },
        "accepts_non_us": {
            "value": extraction_result["accepts_non_us"].value,
            "confidence": extraction_result["accepts_non_us"].confidence
        },
        "screening_required": {
            "value": extraction_result["screening_required"].value,
            "confidence": extraction_result["screening_required"].confidence
        },
        "company_size": {
            "value": extraction_result["company_size"].value,
            "confidence": extraction_result["company_size"].confidence
        },
        "required_skills": {
            "value": extraction_result["required_skills"].value,
            "confidence": extraction_result["required_skills"].confidence
        },
        "preferred_skills": {
            "value": extraction_result["preferred_skills"].value,
            "confidence": extraction_result["preferred_skills"].confidence
        },
        "required_years_experience": {
            "value": extraction_result["required_years_experience"].value,
            "confidence": extraction_result["required_years_experience"].confidence
        },
        "responsibilities": {
            "value": extraction_result["responsibilities"].value,
            "confidence": extraction_result["responsibilities"].confidence
        },
        "metadata": extraction_result["metadata"]
    }

    # Write JSON output
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_dict, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing output file {output_path}: {e}", file=sys.stderr)
        return None

    if verbose:
        print(f"[DEBUG] Output written to {output_path}", file=sys.stderr)

    return output_dict


def get_files_to_process(input_path: Path) -> list[Path]:
    """
    Get list of files to process from input path (file or directory).

    Args:
        input_path: Path to file or directory

    Returns:
        List of file paths to process
    """
    if input_path.is_file():
        return [input_path]
    elif input_path.is_dir():
        # Find all supported files in directory
        files = []
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(input_path.glob(f"*{ext}"))
        # Sort for consistent processing order
        return sorted(files)
    else:
        print(f"Error: Path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)


async def main_async():
    """Main async CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract structured information from job descriptions using DSPy"
    )
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to text file or directory containing job descriptions"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output JSON file path (only used for single file input; default: auto-generated from input filename)"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default=DEFAULT_ENDPOINT,
        help=f"OpenAI-compatible API endpoint URL (default: {DEFAULT_ENDPOINT})"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=4,
        help="Number of files to process in parallel per batch (default: 4, matching llama-server --parallel limit)"
    )

    args = parser.parse_args()

    # Resolve input path
    input_path = Path(args.input_path)

    if not input_path.exists():
        print(f"Error: Path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Get list of files to process
    files_to_process = get_files_to_process(input_path)

    if len(files_to_process) == 0:
        if input_path.is_dir():
            print(f"Warning: No supported files found in directory: {input_path}", file=sys.stderr)
            print(f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"[DEBUG] Found {len(files_to_process)} file(s) to process", file=sys.stderr)
        print(f"[DEBUG] Batch size: {args.batch_size} files per batch", file=sys.stderr)

    # Process files in batches (sequential batches, parallel within batch)
    async def process_file_with_index(file_path: Path, index: int) -> Optional[dict]:
        if args.verbose:
            print(f"\n[DEBUG] Processing file {index + 1}/{len(files_to_process)}: {file_path.name}", file=sys.stderr)

        # For single file, use custom output if provided; for directory, auto-generate
        output_path = None
        if len(files_to_process) == 1 and args.output:
            output_path = Path(args.output)

        result = await process_single_file(
            input_path=file_path,
            output_path=output_path,
            endpoint=args.endpoint,
            verbose=args.verbose
        )

        if result:
            return {
                "input_file": str(file_path),
                "result": result
            }
        return None

    # Split files into batches
    batch_size = args.batch_size
    batches = [
        files_to_process[i:i + batch_size]
        for i in range(0, len(files_to_process), batch_size)
    ]

    if args.verbose:
        print(f"[DEBUG] Split into {len(batches)} batch(es)", file=sys.stderr)

    # Process batches sequentially, files within each batch in parallel
    results = []
    for batch_idx, batch in enumerate(batches):
        if args.verbose:
            print(f"\n[DEBUG] Processing batch {batch_idx + 1}/{len(batches)} ({len(batch)} file(s))", file=sys.stderr)

        # Process files in current batch concurrently
        tasks = [
            process_file_with_index(file_path, idx)
            for idx, file_path in enumerate(batch, start=batch_idx * batch_size)
        ]
        batch_results = await asyncio.gather(*tasks)
        results.extend([r for r in batch_results if r is not None])

    if args.verbose:
        print(f"\n[DEBUG] Successfully processed {len(results)}/{len(files_to_process)} file(s)", file=sys.stderr)

    # If processing multiple files, output summary
    if len(files_to_process) > 1:
        summary = {
            "total_files": len(files_to_process),
            "successful": len(results),
            "failed": len(files_to_process) - len(results),
            "results": results
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    elif len(results) == 1:
        # Single file: print result directly (for backward compatibility)
        print(json.dumps(results[0]["result"], indent=2, ensure_ascii=False))


def main():
    """Main CLI entry point (synchronous wrapper for async main)."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
