# Based on tutorial from the langchain library https://python.langchain.com/docs/tutorials/rag/
# Embedding model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (Modelo especializado em busca por similaridade de texto)
# -- Modelo cria um vetores com 384 dimensões


from db import get_db
from model import question_to_model

if __name__ == "__main__":

    db = get_db(in_memory=False)
    if db is None:
        print("Erro ao criar ou carregar o banco de dados.")
    else:
        while True:
            print ("Seja bem vindo!. Esse é o nosso TutorIA, agente especializado em responder perguntas sobre conceitos de POO.\n")
            question = input("👤 ")
            print ("Pensando...\n")
            answer, sources = question_to_model(db, question)
            formated_response = f"Resposta: {answer}\nFontes:\n{"\n".join(sources)}"
            print(f"🤖 {formated_response}")
