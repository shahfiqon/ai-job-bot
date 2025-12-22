"""HTTP client wrapper for llama-server with Ollama-like interface."""
import requests
from loguru import logger

from app.config import settings


class LlamaServerClient:
    """Wrapper for llama-server HTTP API to provide an Ollama-like interface."""
    
    def __init__(self, host: str | None = None, timeout: int = 120):
        """
        Initialize the llama-server client.
        
        Args:
            host: llama-server URL (default: from settings.LLAMA_SERVER_URL)
            timeout: Request timeout in seconds
        """
        self.host = (host or settings.LLAMA_SERVER_URL).rstrip('/')
        self.timeout = timeout
    
    def generate(self, model: str, prompt: str, options: dict | None = None, **kwargs):
        """
        Generate text using llama-server's completion endpoint.
        
        Args:
            model: Model name (ignored, llama-server uses the loaded model)
            prompt: The prompt to generate from
            options: Generation options (temperature, top_p, num_ctx)
            **kwargs: Additional arguments (ignored for compatibility)
            
        Returns:
            Object with 'response' attribute containing generated text
        """
        opts = options or {}
        
        # Build request payload for llama-server /completion endpoint
        payload = {
            "prompt": prompt,
            "temperature": opts.get("temperature", 0.7),
            "top_p": opts.get("top_p", 0.9),
            "n_predict": opts.get("max_tokens", 2048),  # max tokens to generate
            "stop": ["</s>", "<|im_end|>", "<|eot_id|>"],  # common stop tokens
            "stream": False,
        }
        
        # If num_ctx is specified, include it
        if "num_ctx" in opts:
            payload["n_ctx"] = opts["num_ctx"]
        
        try:
            logger.debug(f"Sending completion request to {self.host}/completion")
            response = requests.post(
                f"{self.host}/completion",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            result = response.json()
            
            # llama-server returns {"content": "generated text", ...}
            # Convert to Ollama-like format
            generated_text = result.get("content", "")
            
            # Return object that mimics Ollama response
            class Response:
                def __init__(self, text):
                    self.response = text
            
            return Response(generated_text)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to llama-server: {e}")
            raise


def Client(host: str | None = None, timeout: int = 120):
    """
    Factory function to create a LlamaServerClient.
    Mimics ollama.Client() for compatibility.
    
    Args:
        host: llama-server URL
        timeout: Request timeout in seconds
        
    Returns:
        LlamaServerClient instance
    """
    return LlamaServerClient(host=host, timeout=timeout)

