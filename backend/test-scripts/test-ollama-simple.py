"""Simple test to verify Ollama connection works"""

from app.utils.ollama_utils import parse_job_description_with_ollama

# Simple short job description
simple_job = """
Software Engineer position.
Requirements:
- 3+ years Python experience
- FastAPI knowledge
- AWS experience

Benefits:
- Remote work
- Competitive salary $120k-150k
"""

print("Testing with simple job description...")
result = parse_job_description_with_ollama(simple_job, timeout=300)
print(f"\nSuccess: {result['success']}")
if result['success']:
    print(f"Data: {result['data']}")
else:
    print(f"Error: {result['error']}")
if result['raw_response']:
    print(f"\nRaw response (first 500 chars): {result['raw_response'][:500]}")

