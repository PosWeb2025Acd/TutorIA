import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Download ollama to import models curl -fsSL https://ollama.com/install.sh | sh
# DOwnload deepseek model. ollama pull deepseek-r1:8b

file_path = [
    os.getcwd() + '/../documents/conceitos_basicos_poo.pdf',
    os.getcwd() + '/../documents/poo_c_plus_plus.pdf',
    os.getcwd() + '/../documents/poo_java.pdf',
    os.getcwd() + '/../documents/revisao_poo.pdf',
]

def load_pages():
    pages = []
    for file in file_path:
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
