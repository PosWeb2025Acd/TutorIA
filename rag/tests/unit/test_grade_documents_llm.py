from rag_graph.context_evaluators import grade_documents_llm

def test_grades_each_document_with_one_llm_call(fake_llm, documents):
    grades = grade_documents_llm("O que é polimorfismo?", documents)

    assert [grade["label"] for grade in grades] == ["relevant", "partially_relevant", "not_relevant"]
    assert len(fake_llm.calls) == len(documents)

def test_prompt_contains_question_and_document(fake_llm, documents):
    grade_documents_llm("O que é polimorfismo?", documents[:1])

    assert "O que é polimorfismo?" in fake_llm.calls[0]
    assert documents[0].page_content in fake_llm.calls[0]

def test_no_documents_means_no_llm_calls(fake_llm):
    assert grade_documents_llm("O que é polimorfismo?", []) == []
    assert fake_llm.calls == []
