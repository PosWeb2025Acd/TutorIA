from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_core.runnables.history import RunnableWithMessageHistory

MODEL = "deepseek-r1:8b"

def contextualize_question_chain(llm, db_retriever):
    """
    This function creates a chain that reformulates the user's question
    to be more suitable for retrieval, taking into account the chat history.
    It uses a language model to understand the context of the conversation
    and reformulate the question accordingly.
    """

    prompt_context = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    propmt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_context),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )
    return create_history_aware_retriever(llm, db_retriever, propmt)

def question_chain(llm):
    """
    This function create creates the chain that process the user question wih
    a context and returns the answer. The context is the most important part of the
    RAG system, as it provides the necessary information to answer the question.
    The context is based on the retrieved information from the vector database.
    The chat history is also part of the prompt template, allowing the model to
    take into account the previous interactions in the conversation.
    """

    prompt = """
    You are an assistant for question-answering tasks related to computer science.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Context: \n\n{context}\n\n\
    Think this step by step and provide a concise answer.
    """

    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ]
    )

    return create_stuff_documents_chain(llm, prompt_template)

def remove_think_set_from_awnser(answer):
    if "</think>" in answer:
        start = answer.index("</think>")
        end = start + len("</think>")
        return answer[end:].strip()

    return answer.strip()

def question_to_model(question, db_retriever, chat_history_store):
    llm = OllamaLLM(model=MODEL, verbose=False, temperature=0.0)

    history_aware_retrieve = contextualize_question_chain(llm, db_retriever)
    user_question_chain = question_chain(llm)
    rag_chain = create_retrieval_chain(history_aware_retrieve, user_question_chain)

    # This is the final part of the chain, which combines the retrieval rag chain
    # with the chat history to provide a complete answer.
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
