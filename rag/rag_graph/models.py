import httpx
import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL")

# Erros levantados quando o Ollama não pode ser alcançado (DNS, conexão recusada, timeout).
# O cliente do Ollama propaga os erros do httpx nas chamadas em streaming e ConnectionError nas demais.
LLM_UNAVAILABLE_ERRORS = (httpx.ConnectError, httpx.TimeoutException, ConnectionError)
