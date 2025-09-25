"""
This module handles the ingestion of historical defect data into the Qdrant vector database.
The data is processed and embedded using OpenAI's embeddings for efficient semantic search.
"""

import os
from dotenv import load_dotenv
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings

load_dotenv()

def ingest_data():
    """
    Loads data from the data directory, splits it into chunks, and ingests it into Qdrant.
    
    The function performs the following steps:
    1. Loads the sample defects text file
    2. Splits the documents into smaller chunks with overlap
    3. Creates embeddings using OpenAI's embedding model
    4. Stores the embeddings in Qdrant
    """
    loader = TextLoader("./data/jira_exports/sample_defects.txt")
    documents = loader.load()
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100, separator="---")
    docs = text_splitter.split_documents(documents)
    
    embeddings = OpenAIEmbeddings()
    
    Qdrant.from_documents(
        docs,
        embeddings,
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        prefer_grpc=True,
        collection_name="historical_defects",
    )
    print("Data ingestion complete.")

if __name__ == "__main__":
    ingest_data()
