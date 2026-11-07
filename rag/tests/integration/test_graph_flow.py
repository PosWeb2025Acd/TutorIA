from unittest.mock import MagicMock

import pytest

from langgraph.checkpoint.memory import InMemorySaver

from rag_graph import rag_graph
from rag_graph.rag_graph import create_graph
from tests.conftest import GENERATED_ANSWER, FakeContextEvaluationRecorder, FakeVectorStore, make_document, NOT_RELEVANT_TEXT, PARTIAL_TEXT, RELEVANT_TEXT

NO_INFORMATION_ANSWER = "Desculpe, mas não tenho informações suficientes para responder a sua pergunta no momento."
CONFIG = {"configurable": {"thread_id": "thread-teste", "user_id": "user-teste"}}
QUESTION_ANSWER_ID = 42

@pytest.fixture
def saved_answers(monkeypatch):
    save = MagicMock(return_value=QUESTION_ANSWER_ID)
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

def test_jev_refuses_when_relevant_chunk_is_below_min_probability(monkeypatch, fake_llm, fake_jev, saved_answers, documents):
    from tests.conftest import RELEVANT_TEXT

    # O JEV ainda escolhe "relevant", mas com só 55% de probabilidade
    fake_jev.probabilities_by_text[RELEVANT_TEXT] = {"0": 0.05, "1": 0.4, "2": 0.55}

    result = run_graph(monkeypatch, "jev", documents)

    assert result["messages"][-1].content == NO_INFORMATION_ANSWER
    assert result["sources"] == []

def ask(graph, question="O que é polimorfismo?"):
    return graph.invoke({"messages": [{"role": "user", "content": question}]}, CONFIG)

def build_graph(monkeypatch, evaluator, documents, recorder):
    monkeypatch.setattr(rag_graph, "vector_store", FakeVectorStore(documents))
    return create_graph(InMemorySaver(), context_evaluator=evaluator, evaluation_recorder=recorder)

@pytest.mark.parametrize("evaluator", ["llm", "jev"])
def test_records_every_retrieved_chunk_linked_to_the_saved_answer(monkeypatch, fake_llm, fake_jev, saved_answers, documents, evaluator):
    recorder = FakeContextEvaluationRecorder()

    ask(build_graph(monkeypatch, evaluator, documents, recorder))

    assert len(recorder.records) == 1
    question_answer_id, evaluation = recorder.records[0]
    assert question_answer_id == QUESTION_ANSWER_ID
    assert evaluation["evaluator"] == evaluator
    assert evaluation["fallback_error"] is None
    assert [chunk["document_id"] for chunk in evaluation["chunks"]] == ["poo.pdf:1:0", "poo.pdf:2:0", "grafos.pdf:1:0"]
    assert [chunk["label"] for chunk in evaluation["chunks"]] == ["relevant", "partially_relevant", "not_relevant"]
    assert [chunk["used"] for chunk in evaluation["chunks"]] == [True, True, False]

def test_llm_record_has_prompt_and_no_probability(monkeypatch, fake_llm, saved_answers, documents):
    recorder = FakeContextEvaluationRecorder()

    ask(build_graph(monkeypatch, "llm", documents, recorder))

    evaluation = recorder.records[0][1]
    assert "grader assessing relevance" in evaluation["config"]["prompt"]
    assert all(chunk["probability"] is None for chunk in evaluation["chunks"])
    assert evaluation["chunks"][0]["details"] == {"raw_label": "RELEVANT"}

def test_jev_record_has_threshold_and_probabilities(monkeypatch, fake_llm, fake_jev, saved_answers, documents):
    recorder = FakeContextEvaluationRecorder()

    ask(build_graph(monkeypatch, "jev", documents, recorder))

    evaluation = recorder.records[0][1]
    assert evaluation["config"]["min_probability"] == 0.7
    assert [chunk["probability"] for chunk in evaluation["chunks"]] == [0.9, 0.7, 0.8]
    assert evaluation["chunks"][0]["details"]["probabilities"]["relevant"] == 0.9

@pytest.mark.parametrize("evaluator", ["llm", "jev"])
def test_refusal_is_recorded_with_no_chunk_used(monkeypatch, fake_llm, fake_jev, saved_answers, evaluator):
    recorder = FakeContextEvaluationRecorder()
    documents = [make_document("poo.pdf:2:0", PARTIAL_TEXT), make_document("grafos.pdf:1:0", NOT_RELEVANT_TEXT)]

    result = ask(build_graph(monkeypatch, evaluator, documents, recorder))

    assert result["messages"][-1].content == NO_INFORMATION_ANSWER
    assert [chunk["label"] for chunk in recorder.records[0][1]["chunks"]] == ["partially_relevant", "not_relevant"]
    assert [chunk["used"] for chunk in recorder.records[0][1]["chunks"]] == [False, False]

def test_refused_turn_records_doubtful_chunk_as_not_used(monkeypatch, fake_llm, fake_jev, saved_answers, documents):
    recorder = FakeContextEvaluationRecorder()
    fake_jev.probabilities_by_text[RELEVANT_TEXT] = {"0": 0.05, "1": 0.4, "2": 0.55}

    ask(build_graph(monkeypatch, "jev", documents, recorder))

    chunk = recorder.records[0][1]["chunks"][0]
    assert (chunk["label"], chunk["probability"], chunk["used"]) == ("relevant", 0.55, False)

def test_jev_failure_is_recorded_as_llm_with_the_error(monkeypatch, fake_llm, fake_jev, saved_answers, documents):
    recorder = FakeContextEvaluationRecorder()
    fake_jev.status_code = 401

    ask(build_graph(monkeypatch, "jev", documents, recorder))

    evaluation = recorder.records[0][1]
    assert evaluation["evaluator"] == "llm"
    assert evaluation["fallback_error"]
    assert "prompt" in evaluation["config"]
    assert [chunk["label"] for chunk in evaluation["chunks"]] == ["relevant", "partially_relevant", "not_relevant"]

def test_later_turn_on_the_llm_route_records_nothing(monkeypatch, fake_llm, saved_answers, documents):
    recorder = FakeContextEvaluationRecorder()
    graph = build_graph(monkeypatch, "llm", documents, recorder)
    ask(graph)
    recorder.records.clear()

    fake_llm.route = "llm"
    ask(graph, "Qual é a capital da França?")

    assert recorder.records == []

def test_evaluation_is_cleared_from_the_state_after_being_recorded(monkeypatch, fake_llm, saved_answers, documents):
    result = ask(build_graph(monkeypatch, "llm", documents, FakeContextEvaluationRecorder()))

    assert result["context_evaluation"] is None

def test_evaluation_left_by_a_crashed_turn_is_not_attached_to_a_new_question(monkeypatch, fake_llm, saved_answers, documents):
    recorder = FakeContextEvaluationRecorder()
    graph = build_graph(monkeypatch, "llm", documents, recorder)

    # O turno falha depois de avaliar: a avaliação fica no checkpoint, sem resposta salva
    saved_answers.side_effect = RuntimeError("falha simulada")
    with pytest.raises(RuntimeError):
        ask(graph, "O que é polimorfismo?")
    assert graph.get_state(CONFIG).values["context_evaluation"] is not None
    saved_answers.side_effect = None

    fake_llm.route = "llm"
    ask(graph, "Qual é a capital da França?")

    assert recorder.records == []

@pytest.mark.parametrize("evaluator", ["llm", "jev"])
def test_recorder_failure_does_not_affect_the_answer(monkeypatch, fake_llm, fake_jev, saved_answers, documents, evaluator):
    recorder = FakeContextEvaluationRecorder(error=RuntimeError("banco indisponível"))

    result = ask(build_graph(monkeypatch, evaluator, documents, recorder))

    assert result["messages"][-1].content == GENERATED_ANSWER
    assert result["sources"] == ["poo.pdf:1:0", "poo.pdf:2:0"]

def test_doubt_between_useful_levels_uses_the_chunk_when_another_allows_the_answer(monkeypatch, fake_llm, fake_jev, saved_answers):
    recorder = FakeContextEvaluationRecorder()
    documents = [make_document("poo.pdf:1:0", RELEVANT_TEXT), make_document("poo.pdf:2:0", PARTIAL_TEXT), make_document("grafos.pdf:1:0", NOT_RELEVANT_TEXT)]
    # O mesmo perfil do chunk que motivou a regra: "relevant" abaixo do corte, mas 0% de "not_relevant"
    fake_jev.probabilities_by_text[PARTIAL_TEXT] = {"0": 0.0, "1": 0.31, "2": 0.69}

    result = ask(build_graph(monkeypatch, "jev", documents, recorder))

    assert result["messages"][-1].content == GENERATED_ANSWER
    assert result["sources"] == ["poo.pdf:1:0", "poo.pdf:2:0"]
    assert PARTIAL_TEXT in next(call for call in fake_llm.calls if "Use only the following pieces" in call)
    chunk = recorder.records[0][1]["chunks"][1]
    assert (chunk["label"], chunk["probability"], chunk["used"]) == ("relevant", 0.69, True)
    assert chunk["details"]["useful_probability"] == 1.0

def test_doubt_between_useful_levels_alone_does_not_allow_an_answer(monkeypatch, fake_llm, fake_jev, saved_answers):
    recorder = FakeContextEvaluationRecorder()
    documents = [make_document("poo.pdf:2:0", PARTIAL_TEXT)]
    fake_jev.probabilities_by_text[PARTIAL_TEXT] = {"0": 0.0, "1": 0.31, "2": 0.69}

    result = ask(build_graph(monkeypatch, "jev", documents, recorder))

    assert result["messages"][-1].content == NO_INFORMATION_ANSWER
    assert result["sources"] == []
