from rag_graph.context_evaluators import filter_graded_documents

def test_keeps_relevant_and_partially_relevant_documents(documents):
    grades = [{"label": "relevant"}, {"label": "partially_relevant"}, {"label": "not_relevant"}]

    result = filter_graded_documents(documents, grades)

    assert result["documents"] == documents[:2]
    assert result["sources"] == ["poo.pdf:1:0", "poo.pdf:2:0"]
    assert result["has_relevant_documents"] is True

def test_relevant_documents_come_before_partially_relevant(documents):
    grades = [{"label": "partially_relevant"}, {"label": "relevant"}, {"label": "not_relevant"}]

    result = filter_graded_documents(documents, grades)

    assert result["sources"] == ["poo.pdf:2:0", "poo.pdf:1:0"]

def test_only_partially_relevant_documents_do_not_allow_an_answer(documents):
    grades = [{"label": "partially_relevant"}, {"label": "partially_relevant"}, {"label": "not_relevant"}]

    result = filter_graded_documents(documents, grades)

    assert len(result["documents"]) == 2
    assert result["has_relevant_documents"] is False

def test_no_relevant_documents(documents):
    grades = [{"label": "not_relevant"}] * 3

    result = filter_graded_documents(documents, grades)

    assert result == {"documents": [], "sources": [], "has_relevant_documents": False}

def test_empty_retrieval():
    assert filter_graded_documents([], []) == {"documents": [], "sources": [], "has_relevant_documents": False}

def test_doubt_between_useful_levels_keeps_the_chunk_but_does_not_allow_an_answer(documents):
    # O caso real que motivou a regra: 0% de chance de não ser relevante
    grades = [{"label": "relevant", "probability": 0.69, "useful_probability": 1.0}, {"label": "not_relevant", "probability": 0.9, "useful_probability": 0.1}, {"label": "not_relevant", "probability": 0.9, "useful_probability": 0.1}]

    result = filter_graded_documents(documents, grades, min_probability=0.7)

    assert result["sources"] == ["poo.pdf:1:0"]
    assert result["has_relevant_documents"] is False

def test_chunks_that_allow_an_answer_come_first(documents):
    grades = [{"label": "relevant", "probability": 0.6, "useful_probability": 0.95}, {"label": "relevant", "probability": 0.9, "useful_probability": 0.99}, {"label": "partially_relevant", "probability": 0.8, "useful_probability": 0.9}]

    result = filter_graded_documents(documents, grades, min_probability=0.7)

    assert result["sources"] == ["poo.pdf:2:0", "poo.pdf:1:0", "grafos.pdf:1:0"]
    assert result["has_relevant_documents"] is True

def test_discards_chunk_likely_to_be_not_relevant(documents):
    grades = [{"label": "relevant", "probability": 0.9, "useful_probability": 0.95}, {"label": "partially_relevant", "probability": 0.45, "useful_probability": 0.6}, {"label": "not_relevant", "probability": 0.9, "useful_probability": 0.1}]

    result = filter_graded_documents(documents, grades, min_probability=0.7)

    assert result["sources"] == ["poo.pdf:1:0"]

def test_not_relevant_label_is_never_used_even_with_a_low_cut(documents):
    grades = [{"label": "not_relevant", "probability": 0.5, "useful_probability": 0.5}] * 3

    result = filter_graded_documents(documents, grades, min_probability=0.3)

    assert result["sources"] == []

def test_values_equal_to_min_probability_pass_both_decisions(documents):
    grades = [{"label": "relevant", "probability": 0.7, "useful_probability": 0.7}, {"label": "partially_relevant", "probability": 0.5, "useful_probability": 0.7}, {"label": "not_relevant", "probability": 0.9, "useful_probability": 0.1}]

    result = filter_graded_documents(documents, grades, min_probability=0.7)

    assert result["sources"] == ["poo.pdf:1:0", "poo.pdf:2:0"]
    assert result["has_relevant_documents"] is True

def test_grades_without_probability_are_always_used(documents):
    grades = [{"label": "relevant"}, {"label": "partially_relevant"}, {"label": "not_relevant"}]

    result = filter_graded_documents(documents, grades, min_probability=0.9)

    assert result["sources"] == ["poo.pdf:1:0", "poo.pdf:2:0"]
    assert result["has_relevant_documents"] is True
