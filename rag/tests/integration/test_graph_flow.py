from unittest.mock import MagicMock

import pytest

from langgraph.checkpoint.memory import InMemorySaver

from rag_graph import rag_graph
from rag_graph.rag_graph import create_graph
from tests.conftest import GENERATED_ANSWER, FakeVectorStore, make_document, NOT_RELEVANT_TEXT, PARTIAL_TEXT

NO_INFORMATION_ANSWER = "Desculpe, mas não tenho informações suficientes para responder a sua pergunta no momento."
CONFIG = {"configurable": {"thread_id": "thread-teste", "user_id": "user-teste"}}

@pytest.fixture
def saved_answers(monkeypatch):
    save = MagicMock()
    monkeypatch.setattr(rag_graph, "get_postgres_connection", MagicMock())
    monkeypatch.setattr(rag_graph, "create_user_question_and_answer", save)
    return save

def run_graph(monkeypatch, evaluator, documents, question="O que é polimorfismo?"):
    monkeypatch.setattr(rag_graph, "vector_store", FakeVectorStore(documents))
    graph = create_graph(InMemorySaver(), context_evaluator=evaluator)
    return graph.invoke({"messages": [{"role": "user", "content": question}]}, CONFIG)

@pytest.mark.parametrize("evaluator", ["llm", "jev"])
def test_answers_with_relevant_context(monkeypatch, fake_llm, fake_jev, saved_answers, documents, evaluator):
    result = run_graph(monkeypatch, evaluator, documents)

    assert result["messages"][-1].content == GENERATED_ANSWER
    assert result["sources"] == ["poo.pdf:1:0", "poo.pdf:2:0"]
    saved_answers.assert_called_once()
    assert saved_answers.call_args.args[1:] == ("user-teste", "O que é polimorfismo?", GENERATED_ANSWER)

@pytest.mark.parametrize("evaluator", ["llm", "jev"])
def test_refuses_to_answer_without_relevant_context(monkeypatch, fake_llm, fake_jev, saved_answers, evaluator):
    documents = [make_document("poo.pdf:2:0", PARTIAL_TEXT), make_document("grafos.pdf:1:0", NOT_RELEVANT_TEXT)]

    result = run_graph(monkeypatch, evaluator, documents)

    assert result["messages"][-1].content == NO_INFORMATION_ANSWER
    assert result["sources"] == []
    saved_answers.assert_called_once()

def test_only_the_selected_evaluator_is_used(monkeypatch, fake_llm, fake_jev, saved_answers, documents):
    run_graph(monkeypatch, "jev", documents)

    assert len(fake_jev.requests) == len(documents)
    assert not any("grader assessing relevance" in call for call in fake_llm.calls)

def test_llm_evaluator_does_not_call_jev(monkeypatch, fake_llm, fake_jev, saved_answers, documents):
    run_graph(monkeypatch, "llm", documents)

    assert fake_jev.requests == []
    assert sum("grader assessing relevance" in call for call in fake_llm.calls) == len(documents)

def test_jev_api_failure_falls_back_to_llm(monkeypatch, fake_llm, fake_jev, saved_answers, documents):
    fake_jev.status_code = 401

    result = run_graph(monkeypatch, "jev", documents)

    assert result["messages"][-1].content == GENERATED_ANSWER
    assert sum("grader assessing relevance" in call for call in fake_llm.calls) == len(documents)
