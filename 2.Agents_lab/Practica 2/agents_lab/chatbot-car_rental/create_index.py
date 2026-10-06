from langchain.indexes import VectorstoreIndexCreator
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import OllamaEmbeddings
import pickle
import os
import time

def create_vector_index():
    """Create and save vector index from the dataset"""
      
    # Create a TextLoader object
    loader = TextLoader("dataset/rentals.csv")
  
    # Create an OllamaEmbeddings object
    # NOTE: llama3.2 is a chat model, not an embedding model - asking Ollama
    # to embed with it fails ("This server does not support embeddings").
    # nomic-embed-text is a dedicated embedding model (ollama pull nomic-embed-text).
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    
    # Create a VectorstoreIndexCreator object
    index_creator = VectorstoreIndexCreator(embedding=embeddings)

    # Call from_loaders method
    index = index_creator.from_loaders([loader])
    
    # Save the index to disk
    os.makedirs("saved_index", exist_ok=True)
    with open("saved_index/vector_index_llama3_2_rentals.pkl", "wb") as f:
        pickle.dump(index, f)
    
    print("Indexing document in vector store completed!")

if __name__ == "__main__":
    create_vector_index()
