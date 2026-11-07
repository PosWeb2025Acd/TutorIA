from rag_graph.context_evaluation_record import build_context_evaluation
from rag_graph.context_evaluators import filter_graded_documents

QUESTION = "O que é polimorfismo?"
LLM_GRADES = [
    {"label": "relevant", "raw_label": "RELEVANT"},
    {"label": "partially_relevant", "raw_label": "partially_relevant"},
    {"label": "not_relevant", "raw_label": "not_relevant"},
]
JEV_GRADES = [
    {"label": "relevant", "probability": 0.55, "useful_probability": 0.6, "score": 1.5, "confidence": 0.8, "probabilities": {"relevant": 0.55}, "input_tokens": 100, "model": "jev-1.13.0"},
    {"label": "partially_relevant", "probability": 0.7, "useful_probability": 0.9, "score": 1.1, "confidence": 0.8, "probabilities": {"partially_relevant": 0.7}, "input_tokens": 100, "model": "jev-1.13.0"},
    {"label": "not_relevant", "probability": 0.8, "useful_probability": 0.2, "score": 0.2, "confidence": 0.8, "probabilities": {"not_relevant": 0.8}, "input_tokens": 100, "model": "jev-1.13.0"},
]

def test_keeps_all_documents_in_retrieval_order(documents):
    evaluation = build_context_evaluation(QUESTION, "llm", {}, documents, LLM_GRADES, [])

    assert [chunk["position"] for chunk in evaluation["chunks"]] == [0, 1, 2]
    assert [chunk["document_id"] for chunk in evaluation["chunks"]] == [document.id for document in documents]
    assert [chunk["content"] for chunk in evaluation["chunks"]] == [document.page_content for document in documents]

def test_llm_grade_has_no_probability_and_keeps_extras_in_details(documents):
    chunk = build_context_evaluation(QUESTION, "llm", {}, documents, LLM_GRADES, [])["chunks"][0]

    assert chunk["label"] == "relevant"
    assert chunk["probability"] is None
    assert chunk["details"] == {"raw_label": "RELEVANT"}

def test_jev_grade_promotes_probability_and_keeps_extras_in_details(documents):
    chunk = build_context_evaluation(QUESTION, "jev", {}, documents, JEV_GRADES, [])["chunks"][0]

    assert chunk["probability"] == 0.55
    assert set(chunk["details"]) == {"useful_probability", "score", "confidence", "probabilities", "input_tokens", "model"}

def test_used_follows_the_given_ids(documents):
    evaluation = build_context_evaluation(QUESTION, "llm", {}, documents, LLM_GRADES, ["poo.pdf:2:0"])

    assert [chunk["used"] for chunk in evaluation["chunks"]] == [False, True, False]

def test_used_agrees_with_the_filter_below_the_threshold(documents):
    kept = filter_graded_documents(documents, JEV_GRADES, 0.7)

    evaluation = build_context_evaluation(QUESTION, "jev", {}, documents, JEV_GRADES, kept["sources"])

    # A chance de o chunk "relevant" ser útil (0.6) fica abaixo do corte, então ele é descartado, apesar do rótulo
    assert [chunk["used"] for chunk in evaluation["chunks"]] == [False, True, False]

def test_carries_run_level_fields_and_defaults_fallback_to_none(documents):
    config = {"model": "m"}

    plain = build_context_evaluation(QUESTION, "llm", config, documents, LLM_GRADES, [])
    fallback = build_context_evaluation(QUESTION, "llm", config, documents, LLM_GRADES, [], "API fora do ar")

    assert (plain["question"], plain["evaluator"], plain["config"], plain["fallback_error"]) == (QUESTION, "llm", config, None)
    assert fallback["fallback_error"] == "API fora do ar"

def test_no_documents_produces_an_empty_record():
    assert build_context_evaluation(QUESTION, "llm", {}, [], [], [])["chunks"] == []
