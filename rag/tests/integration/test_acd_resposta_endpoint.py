from contextlib import contextmanager
from unittest.mock import MagicMock

import httpx
import pytest

from langgraph.checkpoint.memory import InMemorySaver

import main
from api import token
from rag_graph import rag_graph
from tests.conftest import GENERATED_ANSWER, FakeLLM, FakeVectorStore

USER = {"id": "f977139d-9f1a-4bcb-ada6-e00230928559", "usuario": "aluno", "admin": False}

class UnreachableLLM(FakeLLM):
    """
    Simula o Ollama fora da rede: toda chamada falha na resolução de nome, como no incidente do container isolado.
    """

    error: type = httpx.ConnectError

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.calls.append(messages)
        if self.error is httpx.ConnectError:
            raise httpx.ConnectError("[Errno -3] Temporary failure in name resolution", request=httpx.Request("POST", "http://ollama-tutoria:11434/api/chat"))
        raise self.error("Failed to connect to Ollama")

@pytest.fixture
def client(monkeypatch, documents):
    monkeypatch.setattr(token, "JWT_SECRET_KEY", "segredo-de-teste")
    monkeypatch.setattr(token, "get_postgres_connection", MagicMock())
    monkeypatch.setattr(token, "get_user_by_id_and_user", lambda conn, user_id, user: USER)

    @contextmanager
    def in_memory_checkpointer(_connection):
        yield InMemorySaver()

    monkeypatch.setattr(main.PostgresSaver, "from_conn_string", in_memory_checkpointer)
    monkeypatch.setattr(rag_graph, "vector_store", FakeVectorStore(documents))
    monkeypatch.setattr(rag_graph, "get_postgres_connection", MagicMock())
    monkeypatch.setattr(rag_graph, "create_user_question_and_answer", MagicMock())

    return main.service.test_client()

def auth_header():
    return {"Authorization": f"Bearer {token.generate_token(USER)}"}

def use_llm(monkeypatch, llm):
    from rag_graph import context_evaluators

    monkeypatch.setattr(rag_graph, "llm", llm)
    monkeypatch.setattr(context_evaluators, "llm", llm)

@pytest.mark.parametrize("error", [httpx.ConnectError, ConnectionError])
def test_returns_503_when_llm_is_unreachable(monkeypatch, client, error):
    llm = UnreachableLLM(calls=[], error=error)
    use_llm(monkeypatch, llm)

    response = client.post("/acd/resposta", json={"question": "O que é polimorfismo?"}, headers=auth_header())

    assert response.status_code == 503
    assert response.get_json() == {"status": "error", "erro": "O assistente está indisponível no momento. Tente novamente em alguns instantes."}
    assert len(llm.calls) == 1

def test_answers_normally_when_llm_is_available(monkeypatch, client):
    use_llm(monkeypatch, FakeLLM(calls=[]))

    response = client.post("/acd/resposta", json={"question": "O que é polimorfismo?"}, headers=auth_header())

    assert response.status_code == 200
    assert response.get_json()["answer"] == GENERATED_ANSWER

def test_other_errors_are_not_reported_as_llm_unavailable(monkeypatch, client):
    use_llm(monkeypatch, UnreachableLLM(calls=[], error=KeyError))
    main.service.config["PROPAGATE_EXCEPTIONS"] = False

    try:
        response = client.post("/acd/resposta", json={"question": "O que é polimorfismo?"}, headers=auth_header())
    finally:
        main.service.config["PROPAGATE_EXCEPTIONS"] = None

    assert response.status_code == 500

def test_routes_without_llm_keep_working_while_llm_is_unreachable(monkeypatch, client):
    use_llm(monkeypatch, UnreachableLLM(calls=[]))

    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json()["project_name"] == "TutorIA"
