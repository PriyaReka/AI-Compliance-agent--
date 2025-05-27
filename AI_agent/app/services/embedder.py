import os
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
vector_store = Chroma(embedding_function=embeddings, persist_directory="db/chroma")

def add_to_vector_store(chunks):
    vector_store.add_texts(chunks)

def get_vector_store():
    return vector_store
