import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import PINECONE_API_KEY

# Set environment variable for pinecone

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

#Initialize pinecone client
pc = Pinecone(api_key= PINECONE_API_KEY)

# Define embedding models
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

INDEX_NAME = "rag-index"

# retriever fuction
def get_retriever():
    """We are creating a retriever function that:
        Retrieves the most semantically matching embeddings from the vector database
        Creates the Pinecone vector database if it does not already exist
        And finally serves the retrieved context to the LLM for answer generation
    """
    # ensure the index exists, create if not
    if INDEX_NAME not in pc.list_indexes().names():
        print("Create")
        pc.create_index(
            name = INDEX_NAME,
            dimension= 384,
            metric = "cosine",
            spec = ServerlessSpec(cloud='aws', region= 'us-east-1')

        )
        print("Created Pincone index.")

    vectorstore = PineconeVectorStore(index_name= INDEX_NAME, embedding= embeddings)
    return vectorstore.as_retriever()

#Upload documents to vectorstore

def add_document(text_content:str):
    """
     Take raw text. Break it into meaningful chunks
     Convert each chunk into embeddings. Store them inside Pinecone
     Returns the number of chunks added
    """
    if not text_content:
        raise ValueError("Document content cannot be empty!")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200,
        add_start_index = True
    )

    # Create langchain documents object form the raw text
    documents = text_splitter.create_documents([text_content])

    print("Splitting document into chunk for indexing...")

    # get vectorstore instance to add documents
    vectorstore = PineconeVectorStore(index_name= INDEX_NAME, embedding=embeddings)

    # add documents to vectorstore
    vectorstore.add_documents(documents)
    print(f"Successfully added {len(documents)} chunks to pinecone vector store")
    
    return len(documents)


def clear_index():
    """
    Delete all vectors from the Pinecone index
    """
    try:
        index = pc.Index(INDEX_NAME)
        index.delete(delete_all=True)
        print(f"Successfully cleared all vectors from index: {INDEX_NAME}")
    except Exception as e:
        print(f"Error clearing index: {e}")
        raise


