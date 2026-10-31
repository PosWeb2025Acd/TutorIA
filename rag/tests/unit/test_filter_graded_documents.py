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
