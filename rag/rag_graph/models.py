import httpx
import os

from langchain_ollama import ChatOllama

MODEL = "llama3.1:8b"
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL")

llm = ChatOllama(model=MODEL, verbose=False, temperature=0.0, base_url=OLLAMA_BASE_URL)

# Erros levantados quando o Ollama não pode ser alcançado (DNS, conexão recusada, timeout).
# O cliente do Ollama propaga os erros do httpx nas chamadas em streaming e ConnectionError nas demais.
LLM_UNAVAILABLE_ERRORS = (httpx.ConnectError, httpx.TimeoutException, ConnectionError)
