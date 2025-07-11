from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

MODEL = "deepseek-r1:8b"

def question_to_model(results_from_db, question):
    prompt = """
    You are an assistant for question-answering tasks related to computer science. Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Context: {context}
    Answer the question based on the context provided: {question}
    Think this step by step and provide a concise answer.
    """

    context = "\n\n".join([doc.page_content for doc, _ in results_from_db])
    prompt_template = ChatPromptTemplate.from_template(prompt)

    llm = OllamaLLM(model=MODEL, verbose=False, temperature=0.1, stop=["<think></think>"])
    llm_chain = prompt_template | llm

    sources = [doc.metadata["page_id"] for doc, _ in results_from_db]
    return llm_chain.invoke({"context": context, "question": question}), sources
