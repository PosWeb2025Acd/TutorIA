import os

from concurrent.futures import ThreadPoolExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import JsonOutputParser
from typesafe_sdk import Score, TypeSafeClient
from typing_extensions import List

from rag_graph.models import llm

EVALUATION_RELEVANT = "relevant"
EVALUATION_PARTIALLY_RELEVANT = "partially_relevant"
EVALUATION_NOT_RELEVANT = "not_relevant"

JEV_MODEL = os.getenv("JEV_MODEL", "jev-1.13.0")
JEV_MAX_WORKERS = int(os.getenv("JEV_MAX_WORKERS", "4"))
JEV_QUESTION_ID = "relevance"

# Níveis do Score em ordem crescente; o índice de cada nível é o número retornado pelo JEV.
# Descrevem situações (e não graus), como recomendado pela documentação da TypeSafe.
JEV_LEVELS = [
    (EVALUATION_NOT_RELEVANT, "The passage is about a different subject than the query."),
    (EVALUATION_PARTIALLY_RELEVANT, "The passage is about the subject of the query, but does not contain enough information to answer it."),
    (EVALUATION_RELEVANT, "The passage contains information that directly answers the query."),
]
JEV_RELEVANCE_QUESTION = Score(
    instructions="How well does `passage.text` answer `query`? The query and the passage may be written in Portuguese or English.",
    criteria=[description for _, description in JEV_LEVELS],
)

_jev_client = None

def _get_jev_client():
    """
    Cria o cliente da TypeSafe somente quando o JEV é usado, para que importar este módulo não exija TYPESAFE_API_KEY
    """

    global _jev_client
    if _jev_client is None:
        _jev_client = TypeSafeClient(model=JEV_MODEL)

    return _jev_client

def grade_documents_llm(question: str, documents: List[Document]) -> List[dict]:
    """
    Avalia a relevância de cada documento recuperado usando o LLM local (um documento por chamada).
    """

    prompt_data = """
    You are a grader assessing relevance of a retrieved document to a user question.
    Given a user question and retrieved document, determine if the document provider has sufficient context to answer the question accurately.
    To evaluate if the document is relevant, you can check if the document contains keywords related to the user question.
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals
    Give a score 'relevant', 'partially_relevant' or 'not_relevant' to indicate wheter the document is relevant to the question
    Provide the score as a JSON with a single key 'evaluation' and no premable or explaination
    Document to be used for evaluation: {documents}
    Here is the user question: {question}
    """

    prompt = PromptTemplate.from_template(prompt_data)
    retrieval_grader = prompt | llm | JsonOutputParser()

    grades = []
    for doc in documents:
        result = retrieval_grader.invoke({
            "question": question,
            "documents": doc.page_content,
        })
        grades.append({"label": result['evaluation'].lower()})

    return grades

def __grade_document_jev__(question: str, document: Document) -> dict:
    response = _get_jev_client().system_one(
        state={"query": question, "passage": {"id": document.id, "text": document.page_content}},
        questions={JEV_QUESTION_ID: JEV_RELEVANCE_QUESTION},
    )
    answer = response.scores[JEV_QUESTION_ID]
    # Em caso de empate, max() mantém o primeiro nível, ou seja, o menos relevante
    level = max(range(len(JEV_LEVELS)), key=lambda level: answer.probabilities.get(level, 0.0))

    return {
        "label": JEV_LEVELS[level][0],
        "score": answer.score,
        "confidence": answer.confidence,
        "probabilities": {JEV_LEVELS[level][0]: answer.probabilities.get(level, 0.0) for level in range(len(JEV_LEVELS))},
        "input_tokens": response.usage.input_tokens or 0,
        "model": response.model,
    }

def grade_documents_jev(question: str, documents: List[Document], max_workers: int = None) -> List[dict]:
    """
    Avalia a relevância de cada documento recuperado usando o JEV (TypeSafe), uma requisição por documento.
    As requisições rodam em paralelo; max_workers=1 executa de forma sequencial.
    """

    max_workers = max_workers or JEV_MAX_WORKERS
    if not documents:
        return []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        return list(pool.map(lambda doc: __grade_document_jev__(question, doc), documents))

def filter_graded_documents(documents: List[Document], grades: List[dict]) -> dict:
    """
    Mantém os documentos relevantes e parcialmente relevantes. A resposta só é gerada se houver ao menos um relevante.
    """

    relevant_documents = [doc for doc, grade in zip(documents, grades) if grade["label"] == EVALUATION_RELEVANT]
    partially_relevant_documents = [doc for doc, grade in zip(documents, grades) if grade["label"] == EVALUATION_PARTIALLY_RELEVANT]

    filtered_documents = relevant_documents + partially_relevant_documents
    has_relevant_documents = len(relevant_documents) > 0

    return {"documents": filtered_documents, "sources": [doc.id for doc in filtered_documents], "has_relevant_documents": has_relevant_documents}
