import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from db import get_db

# Download ollama to import models curl -fsSL https://ollama.com/install.sh | sh
# DOwnload deepseek model. ollama pull deepseek-r1:8b

file_path = [
    os.getcwd() + '/documents/conceitos_basicos_poo.pdf',
    os.getcwd() + '/documents/poo_c_plus_plus.pdf',
    os.getcwd() + '/documents/poo_java.pdf',
    os.getcwd() + '/documents/revisao_poo.pdf',
]

def __load_pages__():
    pages = []
    for file in file_path:
        loader = PyPDFLoader(file)
        for page in loader.lazy_load():
            pages.append(page)

    return pages

def __create_pages_chunks__(pages, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True
    )
    return text_splitter.split_documents(pages)

def __create_chunk_ids__(chunks):
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        page_id = f"{source}:{page}"

        if last_page_id == page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{page_id}:{current_chunk_index}"
        last_page_id = page_id

        chunk.metadata["page_id"] = chunk_id

    return chunks

def __add_chunks_to_db__(db, chunks):
    ids = [chunk.metadata["page_id"] for chunk in chunks]
    chunks_found = db.get_by_ids(ids)
    chunks_to_add = []
    for chunk in chunks:
        if chunk.metadata["page_id"] not in [c.metadata["page_id"] for c in chunks_found]:
            chunks_to_add.append(chunk)

    if not chunks_to_add:
        print("No new chunks to add to the database.")
        return db

    ids = [chunk.metadata["page_id"] for chunk in chunks_to_add]
    db.add_documents(documents=chunks_to_add, ids=ids)

    return db

if __name__ == "__main__":
    print("Loading pages...")
    pages = __load_pages__()
    print("Creating chunks...")
    chunks = __create_pages_chunks__(pages)
    chunks = __create_chunk_ids__(chunks)

    db = get_db()

    print("Adding chunks to database...")

    __add_chunks_to_db__(db, chunks)

    print("Chunks added to database successfully.")
