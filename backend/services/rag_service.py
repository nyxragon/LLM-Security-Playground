import httpx
import json
import uuid
import os
from typing import Dict, List, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
import PyPDF2
import docx

class RAGService:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/chat"
        self.model = "phi3:mini"
        self.conversations: Dict[str, List[Dict]] = {}
        self.session_documents: Dict[str, List[Dict]] = {}
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collections: Dict[str, chromadb.Collection] = {}
    
    def get_or_create_collection(self, session_id: str):
        """Get or create ChromaDB collection for session"""
        if session_id not in self.collections:
            collection_name = f"session_{session_id.replace('-', '_')}"
            self.collections[session_id] = self.chroma_client.get_or_create_collection(
                name=collection_name
            )
        return self.collections[session_id]
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file formats"""
        text = ""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            elif file_ext == '.pdf':
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
            elif file_ext in ['.doc', '.docx']:
                doc = docx.Document(file_path)
                for paragraph in doc.paragraphs:
                    text += paragraph.text + '\n'
            else:
                # Try to read as text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
        except Exception as e:
            raise Exception(f"Error extracting text from {file_path}: {str(e)}")
        
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
            if i + chunk_size >= len(words):
                break
        
        return chunks
    
    async def add_document(self, file_path: str, session_id: str):
        """Add document to RAG system"""
        try:
            # Extract text from file
            text = self.extract_text_from_file(file_path)
            
            # Chunk the text
            chunks = self.chunk_text(text)
            
            # Get collection for this session
            collection = self.get_or_create_collection(session_id)
            
            # Add chunks to vector store
            doc_id = str(uuid.uuid4())
            filename = os.path.basename(file_path)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                collection.add(
                    documents=[chunk],
                    ids=[chunk_id],
                    metadatas=[{
                        "document_id": doc_id,
                        "filename": filename,
                        "chunk_index": i,
                        "session_id": session_id,
                        "upload_time": datetime.now().isoformat()
                    }]
                )
            
            # Track document in session
            if session_id not in self.session_documents:
                self.session_documents[session_id] = []
            
            self.session_documents[session_id].append({
                "document_id": doc_id,
                "filename": filename,
                "chunk_count": len(chunks),
                "upload_time": datetime.now(),
                "file_path": file_path
            })
            
            return doc_id
        
        except Exception as e:
            raise Exception(f"Error adding document: {str(e)}")
    
    async def retrieve_relevant_chunks(self, query: str, session_id: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant document chunks for query"""
        try:
            collection = self.get_or_create_collection(session_id)
            
            # Query the vector store
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            chunks = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    chunks.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i],
                        "relevance_score": 1.0 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            return chunks
        
        except Exception as e:
            print(f"Error retrieving chunks: {str(e)}")
            return []
    
    async def chat(self, message: str, conversation_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict:
        """Chat with RAG-enabled system"""
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Get or create conversation
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        conversation = self.conversations[conversation_id]
        
        # Retrieve relevant chunks
        relevant_chunks = await self.retrieve_relevant_chunks(message, session_id)
        
        # Build context from retrieved chunks
        context = ""
        sources = []
        if relevant_chunks:
            context = "\n\nRelevant information from uploaded documents:\n"
            for i, chunk in enumerate(relevant_chunks):
                context += f"\n[Source {i+1}: {chunk['metadata']['filename']}]\n{chunk['content']}\n"
                sources.append(chunk['metadata']['filename'])
        
        # Add user message to conversation
        conversation.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now()
        })
        
        # Prepare enhanced prompt with context
        enhanced_message = message
        if context:
            enhanced_message = f"{message}\n{context}\n\nPlease answer based on the provided context when relevant."
        
        # Prepare messages for Ollama
        messages = []
        for msg in conversation[:-1]:  # All previous messages except the current one
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message with context
        messages.append({"role": "user", "content": enhanced_message})
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                assistant_response = result["message"]["content"]
                
                # Add assistant response to conversation
                conversation.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "timestamp": datetime.now(),
                    "rag_context": {
                        "retrieved_chunks": len(relevant_chunks),
                        "sources": sources
                    }
                })
                
                return {
                    "content": assistant_response,
                    "conversation_id": conversation_id,
                    "metadata": {
                        "model": self.model,
                        "mode": "rag",
                        "retrieved_chunks": relevant_chunks,
                        "sources": sources,
                        "tokens_used": result.get("eval_count", 0),
                        "processing_time": result.get("eval_duration", 0) / 1000000
                    }
                }
        
        except httpx.HTTPError as e:
            raise Exception(f"Ollama API error: {str(e)}")
        except Exception as e:
            raise Exception(f"RAG service error: {str(e)}")
    
    async def get_conversation(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])
    
    async def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    async def get_session_documents(self, session_id: str) -> List[Dict]:
        """Get documents for a session"""
        return self.session_documents.get(session_id, [])