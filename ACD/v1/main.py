# Based on tutorial from the langchain library https://python.langchain.com/docs/tutorials/rag/

from process_files import *
from model import question_to_model
from db import add_chunks_to_db_and_return_db

if __name__ == "__main__":
    pages = load_pages()
    chunks = create_pages_chunks(pages)
    chunks = create_chunk_ids(chunks)
    db = add_chunks_to_db_and_return_db(chunks, create_embedding())

    while True:
        question = input("👤 ")
        print ("Pensando...\n")
        answer, sources = question_to_model(db, question)
        formated_response = f"Resposta: {answer}\nFontes:\n{"\n".join(sources)}"
        print(f"🤖 {formated_response}")
