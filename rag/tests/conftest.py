import json
import sys
import types

from unittest.mock import MagicMock

import httpx2
import pytest

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from typesafe_sdk import TypeSafeClient

# Importar rag_graph instancia o vector store (Chroma + modelo de embeddings). Nos testes ele é substituído
# por um stub antes de qualquer import, e cada teste injeta o retriever falso de que precisa.
if "db.chroma" not in sys.modules:
    chroma_stub = types.ModuleType("db.chroma")
    chroma_stub.get_chroma_db = lambda: None
    sys.modules["db.chroma"] = chroma_stub

RELEVANT_TEXT = "Polimorfismo é a capacidade de objetos de classes diferentes responderem à mesma mensagem."
PARTIAL_TEXT = "Programação orientada a objetos organiza o código em classes e objetos."
NOT_RELEVANT_TEXT = "Um grafo é composto por vértices e arestas."
GENERATED_ANSWER = "Polimorfismo permite que objetos diferentes respondam à mesma mensagem."

# Rótulo esperado para cada texto de chunk, usado tanto pelo LLM falso quanto pelo JEV falso
LABEL_BY_TEXT = {
    RELEVANT_TEXT: "relevant",
    PARTIAL_TEXT: "partially_relevant",
    NOT_RELEVANT_TEXT: "not_relevant",
}
PROBABILITIES_BY_LABEL = {
    "not_relevant": {"0": 0.8, "1": 0.15, "2": 0.05},
    "partially_relevant": {"0": 0.1, "1": 0.7, "2": 0.2},
    "relevant": {"0": 0.02, "1": 0.08, "2": 0.9},
}

class FakeLLM(BaseChatModel):
    """
    LLM falso que responde de acordo com o passo do grafo identificado no prompt.
    """

    route: str = "vectorstore"
    calls: list = []

    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        prompt = "\n".join(str(message.content) for message in messages)
        self.calls.append(prompt)

        if "routing user questions" in prompt:
            content = json.dumps({"choice": self.route})
        elif "grader assessing relevance" in prompt:
            label = next((label for text, label in LABEL_BY_TEXT.items() if text in prompt), "not_relevant")
            content = json.dumps({"evaluation": label.upper()})
        else:
            content = GENERATED_ANSWER

        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

class FakeContextEvaluationRecorder:
    """
    Guarda as avaliações em memória; com error, simula uma falha do armazenamento.
    """

    def __init__(self, error=None):
        self.error = error
        self.records = []

    def record(self, question_answer_id, evaluation):
        if self.error:
            raise self.error
        self.records.append((question_answer_id, evaluation))

class FakeRetriever:
    def __init__(self, documents):
        self.documents = documents

    def invoke(self, question):
        return self.documents

class FakeVectorStore:
    def __init__(self, documents):
        self.documents = documents

    def as_retriever(self):
        return FakeRetriever(self.documents)

def make_document(doc_id, text):
    return Document(id=doc_id, page_content=text)

def jev_response(probabilities, input_tokens=100):
    return {
        "model": "jev-1.13.0",
        "answers": {"relevance": {
            "type": "score",
            "score": sum(int(level) * p for level, p in probabilities.items()),
            "confidence": 0.8,
            "legend": {"0": "a", "1": "b", "2": "c"},
            "probabilities": probabilities,
        }},
        "usage": {"input_tokens": input_tokens, "output_tokens": 0},
    }

class FakeJevApi:
    """
    Substitui o servidor da TypeSafe via MockTransport: o cliente real do SDK serializa a requisição
    e desserializa a resposta, mas nada sai da máquina.
    """

    def __init__(self, status_code=200):
        self.status_code = status_code
        self.requests = []
        # Probabilidades específicas por texto de chunk, para simular respostas pouco assertivas
        self.probabilities_by_text = {}

    def handler(self, request):
        body = json.loads(request.content)
        self.requests.append(body)
        if self.status_code != 200:
            return httpx2.Response(self.status_code, json={"error": "falha simulada"})

        text = body["state"]["passage"]["text"]
        probabilities = self.probabilities_by_text.get(text) or PROBABILITIES_BY_LABEL[LABEL_BY_TEXT.get(text, "not_relevant")]
        return httpx2.Response(200, json=jev_response(probabilities))

    def client(self):
        return TypeSafeClient(api_key="test-key", model="jev-1.13.0", transport=httpx2.MockTransport(self.handler))

@pytest.fixture(autouse=True)
def jev_min_probability(monkeypatch):
    """
    Fixa o corte em 0.7 para que os testes não dependam de JEV_MIN_PROBABILITY no ambiente.
    """

    from rag_graph import context_evaluators

    monkeypatch.setattr(context_evaluators, "JEV_MIN_PROBABILITY", 0.7)
    return 0.7

@pytest.fixture(autouse=True)
def no_postgres_for_context_evaluations(monkeypatch):
    """
    O grafo grava no Postgres por padrão; nenhum teste offline deve tentar se conectar.
    """

    from api.context_evaluations import context_evaluations_repository

    monkeypatch.setattr(context_evaluations_repository, "get_postgres_connection", MagicMock())

@pytest.fixture
def documents():
    return [
        make_document("poo.pdf:1:0", RELEVANT_TEXT),
        make_document("poo.pdf:2:0", PARTIAL_TEXT),
        make_document("grafos.pdf:1:0", NOT_RELEVANT_TEXT),
    ]

@pytest.fixture
def fake_llm(monkeypatch):
    from rag_graph import context_evaluators, rag_graph

    llm = FakeLLM(calls=[])
    monkeypatch.setattr(context_evaluators, "llm", llm)
    monkeypatch.setattr(rag_graph, "llm", llm)
    return llm

@pytest.fixture
def fake_jev(monkeypatch):
    from rag_graph import context_evaluators

    api = FakeJevApi()
    client = api.client()
    monkeypatch.setattr(context_evaluators, "_get_jev_client", lambda: client)
    return api
