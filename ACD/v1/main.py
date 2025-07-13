# Based on tutorial from the langchain library https://python.langchain.com/docs/tutorials/rag/
# Embedding model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (Modelo especializado em busca por similaridade de texto)
# -- Modelo cria um vetores com 384 dimensões

from db import get_db
from model import question_to_model

if __name__ == "__main__":

    db = get_db()
    if db is None:
        print("Erro ao criar ou carregar o banco de dados.")
        exit(1)

    print ("Seja bem vindo!. Esse é o nosso TutorIA, agente especializado em responder perguntas sobre conceitos de POO.")
    while True:
        print ("Digite a sua pergunta: ")
        question = input("👤 ")
        print ("Pensando...")

        # k = top 5 results
        result_from_db = db.similarity_search_with_score(query=question, k=3)
        if not result_from_db:
            print("Não encontrei informações relevantes para responder a sua pergunta.")
            continue

        response, sources = question_to_model(result_from_db, question)

        formated_response = f"Resposta: {response[0].answer}\nFontes:\n{"\n".join(sources)}"
        # print(f"🤖 {formated_response}")
