"""Utility functions for interacting with Ollama LLM server."""
import json
from typing import Any

from loguru import logger
from ollama import Client

from app.config import settings
from app.schemas.structured_job import StructuredJobData


SYSTEM_PROMPT = """You are a JSON extraction assistant. Extract structured data from job descriptions.

CRITICAL: Output ONLY a valid JSON object. NO explanations, NO thinking out loud, NO additional text.

Required JSON structure:
{
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1", "skill2"],
  "required_years_experience": integer_or_null,
  "required_education": "string_or_null",
  "preferred_education": "string_or_null",
  "responsibilities": ["item1", "item2"],
  "benefits": ["item1", "item2"],
  "work_arrangement": "Remote|Hybrid|On-site|null",
  "team_size": "string_or_null",
  "technologies": ["tech1", "tech2"],
  "culture_keywords": ["keyword1", "keyword2"],
  "summary": "string_or_null",
  "job_categories": ["category1", "category2"],
  "independent_contractor_friendly": true|false|null,
  "salary_currency": "ISO_code_or_null",
  "salary_min": number_or_null,
  "salary_max": number_or_null,
  "compensation_basis": "Hourly|Annual|Monthly|Contract|Other|null",
  "location_restrictions": ["string1", "string2"],
  "exclusive_location_requirement": true|false|null
}

Job categories MUST be drawn from: "Blockchain/Crypto", "AI/ML", "Data Engineering",
"Full Stack", "Frontend", "Backend", "DevOps/SRE", "Mobile", "Product/Design".
Include every category that clearly applies; leave the array empty if none match.

Set independent_contractor_friendly to:
- true when the posting explicitly mentions 1099, independent contractors, or similar arrangements being accepted.
- false when the posting states contractors/1099 are NOT allowed.
- null if unspecified.

For salary fields:
- Parse any stated salary, rate, or range. Strip currency symbols; set salary_currency to ISO code (default to the most obvious currency such as USD when symbols like $ appear).
- Convert numbers into pure numeric values (e.g., "$120k" -> 120000, "$65/hr" -> 65).
- Populate salary_min and salary_max consistently; use the single value for both bounds if only one number is provided.
- Set compensation_basis to the cadence mentioned (Hourly, Annual, Monthly, Contract, Other) or null if unclear.

List explicit region/country/state requirements in location_restrictions. Set exclusive_location_requirement to true only when the posting clearly says applicants outside the listed areas are NOT accepted; false when it explicitly welcomes multiple regions; null if ambiguous.

Output the JSON object immediately without any preamble or commentary.
"""


USER_PROMPT_TEMPLATE = """Please parse the following job description and return structured data in JSON format:

Job Description:
{description}

Return ONLY the JSON object with the extracted information."""


def check_ollama_model(model_name: str, ollama_url: str | None = None) -> dict[str, Any]:
    """
    Check if a specific model is available on the Ollama server.
    
    Args:
        model_name: Name of the model to check
        ollama_url: Override Ollama server URL
        
    Returns:
        Dictionary with 'available' (bool) and optional 'error' (str)
    """
    base_url = ollama_url or settings.OLLAMA_SERVER_URL
    
    try:
        client = Client(host=base_url)
        models_response = client.list()
        
        # Extract model names from the response
        # The response has a 'models' attribute containing a list of model objects
        models = models_response.get("models", [])
        model_names = []
        for model in models:
            # Each model is an object with a 'model' attribute containing the model name
            if hasattr(model, "model"):
                model_names.append(model.model)
            elif isinstance(model, dict):
                name = model.get("name") or model.get("model", "")
                if name:
                    model_names.append(name)
        
        logger.info(f"Available models from Ollama: {model_names}")
        is_available = model_name in model_names
        
        if not is_available:
            logger.warning(f"Model '{model_name}' not found. Available models: {model_names}")
            return {
                "available": False,
                "error": f"Model '{model_name}' not available. Available models: {', '.join(model_names)}",
            }
        
        logger.info(f"Model '{model_name}' is available on Ollama server")
        return {"available": True}
        
    except Exception as e:
        logger.error(f"Failed to check Ollama models: {e}")
        return {
            "available": False,
            "error": f"Failed to connect to Ollama server: {str(e)}",
        }


def parse_job_description_with_ollama(
    description: str,
    model_name: str = "qwen3:14b",
    timeout: int = 120,
    ollama_url: str | None = None,
    check_model: bool = False,
    use_json_format: bool = False,
) -> dict[str, Any]:
    """
    Parse a job description into structured data using Ollama.
    
    Args:
        description: The raw job description text to parse
        model_name: Name of the Ollama model to use (default: qwen3:14b)
        timeout: Request timeout in seconds (default: 120)
        ollama_url: Override Ollama server URL (uses config if not provided)
        check_model: Whether to check if model exists before making request (default: False)
        use_json_format: Whether to use Ollama's JSON format parameter (default: False)
        
    Returns:
        Dictionary containing:
            - success (bool): Whether parsing succeeded
            - data (StructuredJobData | None): Parsed structured data
            - error (str | None): Error message if parsing failed
            - raw_response (str | None): Raw LLM response for debugging
            
    Example:
        >>> result = parse_job_description_with_ollama(
        ...     "Software Engineer position requiring 5+ years Python experience..."
        ... )
        >>> if result["success"]:
        ...     structured_data = result["data"]
        ...     print(structured_data.required_skills)
    """
    base_url = ollama_url or settings.OLLAMA_SERVER_URL
    
    # Optionally check if the model is available first
    if check_model:
        model_check_result = check_ollama_model(model_name, ollama_url)
        if not model_check_result.get("available", False):
            logger.error(f"Model check failed: {model_check_result.get('error')}")
            return {
                "success": False,
                "data": None,
                "error": model_check_result.get("error", "Model not available"),
                "raw_response": None,
            }
    
    # Prepare the prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(description=description)
    
    try:
        logger.info(f"Sending request to Ollama at {base_url} with model {model_name}")
        
        # Create Ollama client with timeout
        client = Client(host=base_url, timeout=timeout)
        
        # Combine system and user prompts for generate API
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
        
        # Prepare generate parameters
        generate_params = {
            "model": model_name,
            "prompt": full_prompt,
            "options": {
                "temperature": 0.1,  # Low temperature for more consistent output
                "top_p": 0.9,
                "num_ctx": 4096,  # Context window size
            },
        }
        
        # Only include format parameter if requested (some models don't support it well)
        if use_json_format:
            generate_params["format"] = "json"
        
        # Make the generate request (more compatible than chat for some models)
        response = client.generate(**generate_params)
        
        logger.debug(f"Full Ollama response: {response}")
        logger.debug(f"Response type: {type(response)}")
        
        # Extract the response content from generate API
        # The response object has a 'response' attribute containing the generated text
        if hasattr(response, "response"):
            raw_text = response.response
        elif isinstance(response, dict):
            raw_text = response.get("response", "")
        else:
            raw_text = ""
        
        if not raw_text:
            logger.error(f"Empty response from Ollama. Full response: {response}")
            # Check if there's an error message in the response
            error_msg = "Empty response from Ollama server"
            
            return {
                "success": False,
                "data": None,
                "error": error_msg,
                "raw_response": str(response),
            }
        
        logger.debug(f"Raw Ollama response: {raw_text}")
        
        # Try to parse the JSON response
        try:
            # Clean the response - sometimes LLMs add markdown code blocks or extra text
            cleaned_text = raw_text.strip()
            
            # Remove markdown code blocks
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            # Try to find JSON object in the text (handle extra text before/after)
            # Look for the first { and last }
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned_text = cleaned_text[start_idx:end_idx + 1]
            
            parsed_json = json.loads(cleaned_text)
            
            # Validate and create StructuredJobData object
            structured_data = StructuredJobData(**parsed_json)
            
            logger.info("Successfully parsed job description into structured data")
            return {
                "success": True,
                "data": structured_data,
                "error": None,
                "raw_response": raw_text,
            }
            
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse JSON from Ollama response: {json_err}")
            return {
                "success": False,
                "data": None,
                "error": f"Invalid JSON response from LLM: {str(json_err)}",
                "raw_response": raw_text,
            }
        except Exception as validation_err:
            logger.error(f"Failed to validate structured data: {validation_err}")
            return {
                "success": False,
                "data": None,
                "error": f"Data validation error: {str(validation_err)}",
                "raw_response": raw_text,
            }
            
    except Exception as err:
        logger.error(f"Error during Ollama request: {err}")
        return {
            "success": False,
            "data": None,
            "error": f"Failed to connect to Ollama server: {str(err)}",
            "raw_response": None,
        }


async def parse_job_description_async(
    description: str,
    model_name: str = "qwen3:14b",
    timeout: int = 120,
    ollama_url: str | None = None,
) -> dict[str, Any]:
    """
    Async version of parse_job_description_with_ollama.
    
    For FastAPI async endpoints, this runs the synchronous parsing in a thread pool
    to avoid blocking the event loop.
    
    Args:
        description: The raw job description text to parse
        model_name: Name of the Ollama model to use
        timeout: Request timeout in seconds
        ollama_url: Override Ollama server URL
        
    Returns:
        Same as parse_job_description_with_ollama
        
    Example:
        >>> result = await parse_job_description_async(
        ...     "Software Engineer position..."
        ... )
    """
    import asyncio
    
    # Run the blocking function in a thread pool executor
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        parse_job_description_with_ollama,
        description,
        model_name,
        timeout,
        ollama_url,
    )
