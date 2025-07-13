from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from pydantic import BaseModel, Field

MODEL = "deepseek-r1:8b"

class QuestionResponse(BaseModel):
    """Response to a question with sources."""
    answer: str = Field(description="The answer to the question.")
    follow_up_question: str = Field(description="A follow-up question to ask the user.")

def question_to_model(results_from_db, question):
    prompt = """
    You are an assistant for question-answering tasks related to computer science. Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    The response should follow this json schema: {schema}
    Context: {context}
    Answer the question based on the context provided: {question}
    Think this step by step and provide a concise answer.
    """

    parse = PydanticOutputParser(pydantic_object=QuestionResponse)

    context = "\n\n".join([doc.page_content for doc, _ in results_from_db])
    prompt_template = ChatPromptTemplate.from_template(prompt)

    llm = OllamaLLM(model=MODEL, verbose=False, temperature=0.1, stop=["<think></think>"])
    llm_chain = prompt_template | llm | parse

    sources = [doc.metadata["page_id"] for doc, _ in results_from_db]
    model_response = llm_chain.invoke({"context": context, "question": question, "schema": QuestionResponse.model_json_schema()}),
    
    return model_response, sources
