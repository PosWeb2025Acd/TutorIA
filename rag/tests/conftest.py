import json
import sys
import types

import pytest

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

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

# Rótulo esperado para cada texto de chunk, usado pelo LLM falso
LABEL_BY_TEXT = {
    RELEVANT_TEXT: "relevant",
    PARTIAL_TEXT: "partially_relevant",
    NOT_RELEVANT_TEXT: "not_relevant",
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

@pytest.fixture
def documents():
    return [
        make_document("poo.pdf:1:0", RELEVANT_TEXT),
        make_document("poo.pdf:2:0", PARTIAL_TEXT),
        make_document("grafos.pdf:1:0", NOT_RELEVANT_TEXT),
    ]
