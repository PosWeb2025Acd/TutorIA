# Based on tutorial from the langchain library https://python.langchain.com/docs/tutorials/rag/
# Embedding model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (Modelo especializado em busca por similaridade de texto)
# -- Modelo cria um vetores com 384 dimensões

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_ollama import ChatOllama

from db import get_db
from model import question_to_model
from process_files import embedding_model

MODEL = "deepseek-r1:8b"

if __name__ == "__main__":

    db = get_db(embedding_model())
    if db is None:
        print("Erro ao criar ou carregar o banco de dados.")
        exit(1)

    print ("Seja bem vindo!. Esse é o nosso TutorIA, agente especializado em responder perguntas sobre conceitos de POO.")

    db_retriever = db.as_retriever()
    chat_history_store = InMemoryChatMessageHistory()
    llm = ChatOllama(model=MODEL, verbose=False, temperature=0.0)

    while True:
        user_question = input("👤 Digite a sua pergunta (Para finalizar, digite \"sair\"): ")
        if not user_question.strip():
            print("Por favor, digite uma pergunta.")
            continue

        if user_question.strip().lower() == "sair":
            print("🤖 Saindo do assistente. Até logo!")
            break

        print ("🤖 Pensando...")

        try:
            awnser, sources = question_to_model(user_question, db_retriever, chat_history_store, llm)
            formated_response = f"Resposta: {awnser}\nFontes:\n{"\n".join(sources)}"
            print(f"🤖 {formated_response}")
        except Exception as e:
            print(f"Erro ao processar a pergunta: {e}")
            continue
