import json
import os
import logging
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chroma import get_chroma_db

PROCESS_FILES_PATH = os.getcwd() + '/processed_files.json'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_pages():
    directory = os.getcwd() + '/documents'
    file_list = []
    processed_files = get_processed_files()
    for entry in os.listdir(directory):
        if entry == '.gitkeep' or entry in processed_files:
            continue
        full_path = os.path.join(directory, entry)
        if os.path.isfile(full_path):
            file_list.append(full_path) # Or full_path for absolute paths

    pages = []
    for file in file_list:
        loader = PyPDFLoader(file)
        for page in loader.lazy_load():
            pages.append(page)

    return pages

def create_pages_chunks(pages, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True
    )
    return text_splitter.split_documents(pages)

def create_chunk_ids(chunks):
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        file_name = os.path.basename(chunk.metadata.get("source"))
        page = chunk.metadata.get("page")
        page_id = f"{file_name}:{page}"

        if last_page_id == page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        chunk_id = f"{page_id}:{current_chunk_index}"
        last_page_id = page_id

        chunk.metadata["page_id"] = chunk_id
        chunk.metadata["file_name"] = file_name

    return chunks

def add_chunks_to_db(db, chunks):
    ids = [chunk.metadata["page_id"] for chunk in chunks]
    chunks_found = db.get_by_ids(ids)
    chunks_to_add = []
    for chunk in chunks:
        if chunk.metadata["page_id"] not in [c.metadata["page_id"] for c in chunks_found]:
            chunks_to_add.append(chunk)

    if not chunks_to_add:
        print("No new chunks to add to the database.")
        return db

    ids = []
    files_added = []
    for chunk in chunks_to_add:
        if chunk.metadata["file_name"] not in files_added:
            files_added.append(chunk.metadata["file_name"])
        ids.append(chunk.metadata["page_id"])

    db.add_documents(documents=chunks_to_add, ids=ids)
    save_processed_files(files_added)

    return db

def save_processed_files(file_list: list):
    files_processed = get_processed_files()
    file_list.extend(files_processed)
    with open(PROCESS_FILES_PATH, 'w') as f:
        json.dump(file_list, f, indent=2)

def get_processed_files():
    if os.path.exists(PROCESS_FILES_PATH):
        try:
            with open(PROCESS_FILES_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Erro ao recuperar arquivos processados: {e}")
            return {}
    return {}

if __name__ == "__main__":
    while True:
        logger.info("Loading pages...")
        pages = load_pages()
        if pages:
            logger.info("Creating chunks...")
            chunks = create_pages_chunks(pages)
            chunks = create_chunk_ids(chunks)

            db = get_chroma_db()

            logger.info("Adding chunks to database...")
            add_chunks_to_db(db, chunks)
            logger.info("Chunks added to database successfully.")
        else:
            logger.info("Não existem arquivos a serem processados")
        time.sleep(15)
