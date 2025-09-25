from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from dotenv import load_dotenv

def test_qdrant_connection():
    load_dotenv()
    
    # Initialize Qdrant client
    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    
    try:
        # Create a test collection
        collection_name = "test_collection"
        
        # Check if collection exists and delete it
        collections = client.get_collections().collections
        if any(collection.name == collection_name for collection in collections):
            client.delete_collection(collection_name=collection_name)
        
        # Create a new collection
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )
        
        print("✅ Successfully created test collection")
        
        # Clean up
        client.delete_collection(collection_name=collection_name)
        print("✅ Successfully cleaned up test collection")
        
        print("✅ Qdrant connection test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Qdrant connection: {str(e)}")
        return False

if __name__ == "__main__":
    test_qdrant_connection()
