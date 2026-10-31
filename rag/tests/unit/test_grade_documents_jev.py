import httpx2
import pytest

from typesafe_sdk import TypeSafeAuthenticationError, TypeSafeClient, TypeSafeError

from rag_graph import context_evaluators
from rag_graph.context_evaluators import JEV_LEVELS, grade_documents_jev
from tests.conftest import FakeJevApi, jev_response

def use_client(monkeypatch, handler):
    client = TypeSafeClient(api_key="test-key", model="jev-1.13.0", transport=httpx2.MockTransport(handler))
    monkeypatch.setattr(context_evaluators, "_get_jev_client", lambda: client)

def test_maps_most_probable_level_to_label(fake_jev, documents):
    grades = grade_documents_jev("O que é polimorfismo?", documents)

    assert [grade["label"] for grade in grades] == ["relevant", "partially_relevant", "not_relevant"]

def test_sends_query_and_passage_in_state_with_a_score_question(fake_jev, documents):
    grade_documents_jev("O que é polimorfismo?", documents[:1])

    request = fake_jev.requests[0]
    assert request["model"] == "jev-1.13.0"
    assert request["state"] == {"query": "O que é polimorfismo?", "passage": {"id": "poo.pdf:1:0", "text": documents[0].page_content}}
    question = request["questions"]["relevance"]
    assert question["type"] == "score"
    assert question["criteria"] == [description for _, description in JEV_LEVELS]

def test_one_request_per_document(fake_jev, documents):
    grade_documents_jev("O que é polimorfismo?", documents)

    assert len(fake_jev.requests) == len(documents)

@pytest.mark.parametrize("max_workers", [1, 4])
def test_keeps_document_order(fake_jev, documents, max_workers):
    reversed_documents = documents[::-1]

    grades = grade_documents_jev("O que é polimorfismo?", reversed_documents, max_workers=max_workers)

    assert [grade["label"] for grade in grades] == ["not_relevant", "partially_relevant", "relevant"]

def test_returns_confidence_probabilities_and_usage(fake_jev, documents):
    grade = grade_documents_jev("O que é polimorfismo?", documents[:1])[0]

    assert grade["confidence"] == 0.8
    assert grade["probabilities"] == {"not_relevant": 0.02, "partially_relevant": 0.08, "relevant": 0.9}
    assert grade["score"] == pytest.approx(1.88)
    assert grade["input_tokens"] == 100
    assert grade["model"] == "jev-1.13.0"

def test_tie_resolves_to_the_less_relevant_level(monkeypatch, documents):
    use_client(monkeypatch, lambda request: httpx2.Response(200, json=jev_response({"0": 0.1, "1": 0.45, "2": 0.45})))

    grades = grade_documents_jev("O que é polimorfismo?", documents[:1])

    assert grades[0]["label"] == "partially_relevant"

def test_no_documents_means_no_requests(fake_jev):
    assert grade_documents_jev("O que é polimorfismo?", []) == []
    assert fake_jev.requests == []

def test_api_errors_are_propagated(monkeypatch, documents):
    api = FakeJevApi(status_code=401)
    use_client(monkeypatch, api.handler)

    with pytest.raises(TypeSafeAuthenticationError):
        grade_documents_jev("O que é polimorfismo?", documents)

def test_missing_api_key_only_fails_when_jev_is_used(monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setattr(context_evaluators, "_jev_client", None)

    with pytest.raises(TypeSafeError):
        context_evaluators._get_jev_client()
