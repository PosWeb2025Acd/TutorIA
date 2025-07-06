import chromadb
from chromadb.config import Settings
import chromadb.errors

DATABASE_NAME = "tutor_ia"
DATABASE_TUTOR_IA_ACD_COLLECTION = "acd_collection"

def create_database_if_not_exists(database_name):
    client = chromadb.AdminClient(Settings(anonymized_telemetry=False))
    try:
        client.get_database(name=database_name)
    except chromadb.errors.NotFoundError:
        client.create_database(name=database_name)

if __name__ == "__main__":
    create_database_if_not_exists(DATABASE_NAME)

    client = chromadb.Client(
        settings=Settings(anonymized_telemetry=False),
        database=DATABASE_NAME
    )

    collection = client.create_collection(name=DATABASE_TUTOR_IA_ACD_COLLECTION)
    collection.add(
        ids=["1", "2", "3", "4"],
        documents=[
            "Fluminense Footbal Club, é um clube de futebol brasileiro, sediado na cidade do Rio de Janeiro, fundado em 21 de julho de 1902.",
            "O Fluminense é um dos clubes mais tradicionais do Brasil, com uma rica história e uma grande base de torcedores.",
            "Manchescter City é um clube de futebol inglês, sediado na cidade de Manchester, fundado em 1880 como St. Mark's (West Gorton).",
            "Em 2022 o Manchester City conquistou a Premier League, a FA Cup e a UEFA Champions League, completando o triplete.",
        ]
    )
    query = "Como foi o manchester city na temporada 2022?"
    result = collection.query(
        query_texts=[query],
        n_results=4
    )
    result

    documents = result['documents'][0]
    ids = result['ids'][0]

    for document, id in zip(documents, ids):
        print(f"ID: {id}, Document: {document}")
