from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

MODEL = "deepseek-r1:8b"

def prompt_template():
    prompt = """
    You are an assistant for question-answering tasks related to computer science.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Context: \n\n{context}\n\n\
    Think this step by step and provide a concise answer.
    """

    return ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            ("human", "{input}"),
        ]
    )

def reformulate_question_based_on_chat_history(chat_history, question):
    """
    Create a chat history. The chat history will create context for the follow-up questions that the use may ask

    Asks the llm model to reformulate the question based on the chat history from the user
    :param chat_history: The chat history from the user.
    :param question: The question to reformulate.
    :return: The reformulated question.
    """

def remove_think_set_from_awnser(answer):
    if "</think>" in answer:
        start = answer.index("</think>")
        end = start + len("</think>")
        return answer[end:].strip()

    return answer.strip()

def question_to_model(db_retriever, question):
    llm = OllamaLLM(model=MODEL, verbose=False, temperature=0.0)

    prompt = prompt_template()

    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(db_retriever, combine_docs_chain)
    rag_chain = rag_chain 

    model_response = rag_chain.invoke({"input": question})
    answer = model_response["answer"]
    answer = remove_think_set_from_awnser(answer)

    sources = []
    for doc in model_response["context"]:
        sources.append(doc.id)

    return answer, sources


