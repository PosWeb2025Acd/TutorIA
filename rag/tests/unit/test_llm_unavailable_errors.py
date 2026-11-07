import httpx

from rag_graph.models import LLM_UNAVAILABLE_ERRORS

def test_covers_dns_connection_and_timeout_failures():
    request = httpx.Request("POST", "http://ollama-tutoria:11434/api/chat")

    assert isinstance(httpx.ConnectError("Temporary failure in name resolution", request=request), LLM_UNAVAILABLE_ERRORS)
    assert isinstance(httpx.ReadTimeout("timeout", request=request), LLM_UNAVAILABLE_ERRORS)
    assert isinstance(ConnectionError("Failed to connect to Ollama"), LLM_UNAVAILABLE_ERRORS)

def test_does_not_cover_other_errors():
    assert not isinstance(ValueError("JSON inválido"), LLM_UNAVAILABLE_ERRORS)
    assert not isinstance(KeyError("choice"), LLM_UNAVAILABLE_ERRORS)
