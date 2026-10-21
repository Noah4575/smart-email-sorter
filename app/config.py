import os
from dotenv import load_dotenv
from langchain_litellm.chat_models import ChatLiteLLM

load_dotenv()

# Configuration pour utiliser Ollama localement via LiteLLM
# LiteLLM interprète le préfixe "ollama/" pour router vers ton serveur local

raw_model = os.getenv("LLM_MODEL", "phi4-mini")
LLM_MODEL_NAME = raw_model if raw_model.startswith("ollama/") else f"ollama/{raw_model}"

OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")

def get_llm(temperature: float = 0.0):
    return ChatLiteLLM(
        model=LLM_MODEL_NAME,
        api_base=OLLAMA_API_BASE,
        temperature=temperature
    )