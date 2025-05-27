from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, Docx2txtLoader, PyPDFLoader
import os
from datetime import datetime
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DocumentProcessor:
    def __init__(self):
        self.supported_extensions = {
            '.txt': TextLoader,
            '.docx': Docx2txtLoader,
            '.pdf': PyPDFLoader
        }
    
    def process_document(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file extension: {ext}")
        
        loader = self.supported_extensions[ext](file_path)
        return loader.load()[0].page_content

class RAGPipeline:
    def __init__(self, persist_directory: str = "data/chroma_db"):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.embeddings = OpenAIEmbeddings()
        self.persist_directory = persist_directory
        self.vector_store = None
        self.document_processor = DocumentProcessor()
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
    def process_and_store(self, documents: List[str], metadata: List[Dict[str, Any]] = None):
        if not documents:
            raise ValueError("No documents provided")
            
        # Split documents into chunks
        chunks = self.text_splitter.create_documents(documents, metadatas=metadata)
        
        # Create or load vector store
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # Persist the vector store
        self.vector_store.persist()
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Please process documents first.")
        
        # Perform similarity search
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': float(score)
            })
        
        return formatted_results

class PromptAssembler:
    def __init__(self):
        self.template = """
        Based on the following context and query, provide a detailed response:
        
        Context:
        {context}
        
        Query: {query}
        
        Please analyze the information and provide a comprehensive answer.
        """
    
    def assemble(self, context: List[Dict[str, Any]], query: str) -> str:
        # Combine context documents
        combined_context = "\n\n".join([doc['content'] for doc in context])
        
        # Format prompt
        prompt = self.template.format(
            context=combined_context,
            query=query
        )
        
        return prompt

class GeminiResultParser:
    def __init__(self):
        self.flag_keywords = [
            'urgent', 'critical', 'important', 'action required',
            'deadline', 'immediate attention', 'high priority'
        ]
    
    def parse(self, result: str) -> Dict[str, Any]:
        # Check for flags
        flags = []
        for keyword in self.flag_keywords:
            if keyword.lower() in result.lower():
                flags.append(keyword)
        
        return {
            'result': result,
            'has_flags': len(flags) > 0,
            'flags': flags,
            'timestamp': datetime.now().isoformat()
        } 
from services.compliance_flagger import GeminiComplianceFlagger

# Initialize once (e.g., at app startup)
flagger = GeminiComplianceFlagger()

# For each document/email/text you want to check:
risks_and_suggestions = flagger.flag_risks(document_text)
print(risks_and_suggestions)