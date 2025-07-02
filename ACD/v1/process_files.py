import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

# Download ollama to import models curl -fsSL https://ollama.com/install.sh | sh
# DOwnload deepseek model. ollama pull deepseek-r1:8b

HUGGING_FACE_TOKEN = ""
MODEL = "deepseek-r1:8b"
DB_PATH = os.getcwd() + '/rag_db'

os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGING_FACE_TOKEN

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

def create_embedding():
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

def add_chunks_to_db_and_return_db(chunks, embedding):
    if os.path.exists(DB_PATH):
        db = InMemoryVectorStore.load(path=DB_PATH, embedding=embedding)
        print(f"Loaded existing database from {DB_PATH}")
    else:
        db = InMemoryVectorStore(embedding=embedding)
        ids = [chunk.metadata["page_id"] for chunk in chunks]
        db.add_documents(chunks, ids)
        db.dump(DB_PATH)

    return db

def question_to_model(db: InMemoryVectorStore, question) -> str:
    prompt = """
    You are an assistant for question-answering tasks related to computer science. Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Context: {context}
    Answer the question based on the context provided: {question}
    Think this step by step and provide a concise answer.
    """

    # k = top 5 results 
    results = db.similarity_search_with_score(query=question, k=5)
    context = "\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(prompt)

    llm = OllamaLLM(model=MODEL, verbose=False, temperature=0.1, stop=["<think></think>"])
    llm_chain = prompt_template | llm

    sources = [doc.metadata["page_id"] for doc, _ in results]
    return llm_chain.invoke({"context": context, "question": question}), sources

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
