from app.services.embedder import get_vector_store

def retrieve_documents(query, k=5):
    vector_store = get_vector_store()
    return [doc.page_content for doc in vector_store.similarity_search(query, k=k)]

def assemble_prompt(query, docs):
    context = '\n'.join(docs)
    return f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
