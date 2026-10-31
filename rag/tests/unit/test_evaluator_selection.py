import pytest

from langgraph.checkpoint.memory import InMemorySaver

from rag_graph import rag_graph
from rag_graph.rag_graph import create_graph
from tests.conftest import FakeJevApi

def evaluator_of(graph):
    return graph.builder.nodes["retrieved_context_evaluator"].runnable.func

def test_default_evaluator_is_llm(monkeypatch):
    monkeypatch.delenv("CONTEXT_EVALUATOR", raising=False)

    graph = create_graph(InMemorySaver())

    assert evaluator_of(graph) is rag_graph.__retrieved_context_evaluator_llm__

def test_evaluator_from_env_var(monkeypatch):
    monkeypatch.setenv("CONTEXT_EVALUATOR", "JEV")

    graph = create_graph(InMemorySaver())

    assert evaluator_of(graph) is rag_graph.__retrieved_context_evaluator_jev__

def test_parameter_overrides_env_var(monkeypatch):
    monkeypatch.setenv("CONTEXT_EVALUATOR", "jev")

    graph = create_graph(InMemorySaver(), context_evaluator="llm")

    assert evaluator_of(graph) is rag_graph.__retrieved_context_evaluator_llm__

def test_invalid_evaluator_raises():
    with pytest.raises(ValueError):
        create_graph(InMemorySaver(), context_evaluator="gpt")

def test_jev_evaluator_falls_back_to_llm_when_api_fails(monkeypatch, fake_llm, documents):
    from rag_graph import context_evaluators

    api = FakeJevApi(status_code=401)
    client = api.client()
    monkeypatch.setattr(context_evaluators, "_get_jev_client", lambda: client)
    state = {"messages": [type("Message", (), {"content": "O que é polimorfismo?"})()], "documents": documents}

    result = rag_graph.__retrieved_context_evaluator_jev__(state)

    assert len(api.requests) >= 1
    assert len(fake_llm.calls) == len(documents)
    assert result["sources"] == ["poo.pdf:1:0", "poo.pdf:2:0"]
    assert result["has_relevant_documents"] is True
