from fastapi import FastAPI
from app.services.scheduler import start_scheduler

app = FastAPI()

@app.get("/status")
def get_status():
    return {"status": "Running", "flags": []}

@app.get("/ask")
def ask(query: str):
    from app.services.retriever import retrieve_documents, assemble_prompt
    from app.services.generator import generate_response

    docs = retrieve_documents(query)
    prompt = assemble_prompt(query, docs)
    response = generate_response(prompt)
    return {"answer": response}

start_scheduler()
