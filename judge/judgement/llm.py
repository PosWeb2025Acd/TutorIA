import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama

# TODO: Alterar o modelo
MODEL="llama3.1:8b"
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL")

llm = ChatOllama(model=MODEL, verbose=False, temperature=0.0, base_url=OLLAMA_BASE_URL)

def evaluation_from_llm(question_to_evaluate, answer_to_evaluate) -> dict:
    """
    Uses an llm to evaluate if an answer successfully responds to an question
    """

    prompt = """
    You are a grader assessing wheather an answer is userful to resolve a question. Give an grade score as an float on a scale of 0 to 10
    , where 0 is when the answer is completely not useful to the question and 10 is when answer is complete useful to the questio. Provide
    the response as an JSON, with no preamble or explanation with two keys: score, and reasoning. The reasoning key should contain the explanation on why
    that score was provided.

    Here is the answer: {answer}
    Here is the question: {question}
    """
    llm_chain = ChatPromptTemplate.from_template(prompt) | llm | JsonOutputParser()

    return llm_chain.invoke({"answer": answer_to_evaluate, "question": question_to_evaluate})
