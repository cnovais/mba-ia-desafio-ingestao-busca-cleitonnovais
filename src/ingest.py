import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_ollama import OllamaEmbeddings
                                     

load_dotenv()

# Variáveis
PDF_PATH = os.getenv("PDF_PATH")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
PG_VECTOR_COLLECTION_NAME = os.getenv("PG_VECTOR_COLLECTION_NAME")
DATABASE_URL = os.getenv("DATABASE_URL")


def ingest_pdf():

    print(f"Inserindo dados no banco de dados {PG_VECTOR_COLLECTION_NAME}")
    # carregando PDF
    loadPDF = PyPDFLoader(str(PDF_PATH))
    document = loadPDF.load()

    #segmentando o PDF(Chunks)
    document_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    document_chunks = document_splitter.split_documents(document)


    #Gerando um indice 
    content = [
        Document(
            page_content=d.page_content,
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)}
        )
        for d in document_chunks
    ]

    #Gerando ids do documento
    ids = [f"id_{i}" for i in range(len(content))]

    #transformando o conteudo em embeddings
    embeddings = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL)

    #Inserindo os dados no banco de dados
    store = PGVector(
        collection_name=PG_VECTOR_COLLECTION_NAME,
        embeddings=embeddings,
        connection=DATABASE_URL,
        use_jsonb=True
    )
    store.add_documents(documents=content, ids=ids)

    print(f"Dados inseridos no banco de dados {PG_VECTOR_COLLECTION_NAME}")


if __name__ == "__main__":
    ingest_pdf()