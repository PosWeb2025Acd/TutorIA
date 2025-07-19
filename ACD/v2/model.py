from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

MODEL = "deepseek-r1:8b"


def contextualize_question_prompt():
    prompt_context = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    return ChatPromptTemplate.from_messages(
        [
            ("system", prompt_context),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

def question_prompt():
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
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

def remove_think_set_from_awnser(answer):
    if "</think>" in answer:
        start = answer.index("</think>")
        end = start + len("</think>")
        return answer[end:].strip()

    return answer.strip()

def question_to_model(db_retriever, question):
    llm = OllamaLLM(model=MODEL, verbose=False, temperature=0.0)

    prompt_contextualize_question = contextualize_question_prompt()
    history_aware_retrieve = create_history_aware_retriever(llm, db_retriever, prompt_contextualize_question)
    
    prompt = question_prompt()
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)

    rag_chain = create_retrieval_chain(history_aware_retrieve, combine_docs_chain)

    chat_history_store = InMemoryChatMessageHistory()

    model_with_history = RunnableWithMessageHistory(
        rag_chain,
        lambda _ : chat_history_store, # lambda transaforma parametro numa função anonima
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )

    model_response = model_with_history.invoke({"input": question}, config={"configurable": {"session_id": "123"}})
    answer = model_response["answer"]
    answer = remove_think_set_from_awnser(answer)

    sources = []
    for doc in model_response["context"]:
        sources.append(doc.id)

    return answer, sources
