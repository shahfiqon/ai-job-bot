"""Check available Ollama models"""

from app.utils.ollama_utils import check_ollama_model
from ollama import Client
from app.config import settings

client = Client(host=settings.OLLAMA_SERVER_URL)
models_response = client.list()

print("Available Ollama models:")
print("=" * 50)
for model in models_response.get("models", []):
    if hasattr(model, "model"):
        print(f"  - {model.model}")
        if hasattr(model, "details") and hasattr(model.details, "parameter_size"):
            print(f"    Size: {model.details.parameter_size}")
print("=" * 50)

