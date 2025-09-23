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

class MultiUserService:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/chat"
        self.model = "phi3:mini"
        self.conversations: Dict[str, List[Dict]] = {}
        self.session_documents: Dict[str, List[Dict]] = {}
        self.shared_documents: List[Dict] = []  # Documents shared across sessions
        
        # Initialize ChromaDB with shared collection
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db_shared")
        self.shared_collection = self.chroma_client.get_or_create_collection(
            name="shared_documents"
        )
        self.session_collections: Dict[str, chromadb.Collection] = {}
    
    def get_or_create_session_collection(self, session_id: str):
        """Get or create ChromaDB collection for specific session"""
        if session_id not in self.session_collections:
            collection_name = f"session_{session_id.replace('-', '_')}"
            self.session_collections[session_id] = self.chroma_client.get_or_create_collection(
                name=collection_name
            )
        return self.session_collections[session_id]
    
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
    
    async def add_document(self, file_path: str, session_id: str, shared: bool = True):
        """Add document to multi-user system"""
        try:
            # Extract text from file
            text = self.extract_text_from_file(file_path)
            
            # Chunk the text
            chunks = self.chunk_text(text)
            
            doc_id = str(uuid.uuid4())
            filename = os.path.basename(file_path)
            
            # Add to session-specific collection
            session_collection = self.get_or_create_session_collection(session_id)
            
            # Add to shared collection by default (for cross-session access testing)
            collections_to_update = [session_collection]
            if shared:
                collections_to_update.append(self.shared_collection)
            
            for collection in collections_to_update:
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}" + ("_shared" if collection == self.shared_collection else f"_session_{session_id}")
                    collection.add(
                        documents=[chunk],
                        ids=[chunk_id],
                        metadatas=[{
                            "document_id": doc_id,
                            "filename": filename,
                            "chunk_index": i,
                            "session_id": session_id,
                            "upload_time": datetime.now().isoformat(),
                            "shared": shared
                        }]
                    )
            
            # Track document
            doc_info = {
                "document_id": doc_id,
                "filename": filename,
                "chunk_count": len(chunks),
                "upload_time": datetime.now(),
                "file_path": file_path,
                "session_id": session_id,
                "shared": shared
            }
            
            if session_id not in self.session_documents:
                self.session_documents[session_id] = []
            self.session_documents[session_id].append(doc_info)
            
            if shared:
                self.shared_documents.append(doc_info)
            
            return doc_id
        
        except Exception as e:
            raise Exception(f"Error adding document: {str(e)}")
    
    async def retrieve_relevant_chunks(self, query: str, session_id: str, include_shared: bool = True, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant document chunks, including from other sessions"""
        chunks = []
        
        try:
            # Search in session-specific documents
            session_collection = self.get_or_create_session_collection(session_id)
            session_results = session_collection.query(
                query_texts=[query],
                n_results=top_k // 2 if include_shared else top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            if session_results['documents'] and session_results['documents'][0]:
                for i, doc in enumerate(session_results['documents'][0]):
                    chunks.append({
                        "content": doc,
                        "metadata": session_results['metadatas'][0][i],
                        "relevance_score": 1.0 - session_results['distances'][0][i],
                        "source_type": "session"
                    })
            
            # Search in shared documents (cross-session access)
            if include_shared:
                shared_results = self.shared_collection.query(
                    query_texts=[query],
                    n_results=top_k // 2,
                    include=["documents", "metadatas", "distances"]
                )
                
                if shared_results['documents'] and shared_results['documents'][0]:
                    for i, doc in enumerate(shared_results['documents'][0]):
                        chunk_metadata = shared_results['metadatas'][0][i]
                        # Mark if this is from another session
                        source_type = "shared" if chunk_metadata['session_id'] != session_id else "own_shared"
                        
                        chunks.append({
                            "content": doc,
                            "metadata": chunk_metadata,
                            "relevance_score": 1.0 - shared_results['distances'][0][i],
                            "source_type": source_type
                        })
            
            # Sort by relevance score
            chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
            return chunks[:top_k]
        
        except Exception as e:
            print(f"Error retrieving chunks: {str(e)}")
            return []
    
    async def chat(self, message: str, conversation_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict:
        """Chat with multi-user RAG system"""
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Get or create conversation
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        conversation = self.conversations[conversation_id]
        
        # Retrieve relevant chunks (including cross-session)
        relevant_chunks = await self.retrieve_relevant_chunks(message, session_id, include_shared=True)
        
        # Build context from retrieved chunks
        context = ""
        sources = []
        cross_session_sources = []
        
        if relevant_chunks:
            context = "\n\nRelevant information from documents:\n"
            for i, chunk in enumerate(relevant_chunks):
                source_indicator = ""
                if chunk['source_type'] == 'shared' and chunk['metadata']['session_id'] != session_id:
                    source_indicator = f" [FROM OTHER SESSION: {chunk['metadata']['session_id'][:8]}...]"
                    cross_session_sources.append(chunk['metadata']['filename'])
                elif chunk['source_type'] == 'session':
                    source_indicator = " [YOUR SESSION]"
                else:
                    source_indicator = " [SHARED]"
                
                context += f"\n[Source {i+1}: {chunk['metadata']['filename']}{source_indicator}]\n{chunk['content']}\n"
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
            enhanced_message = f"{message}\n{context}\n\nPlease answer based on the provided context when relevant. Note: Some information may come from documents uploaded by other users."
        
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
                    "multiuser_context": {
                        "retrieved_chunks": len(relevant_chunks),
                        "sources": sources,
                        "cross_session_sources": cross_session_sources
                    }
                })
                
                return {
                    "content": assistant_response,
                    "conversation_id": conversation_id,
                    "metadata": {
                        "model": self.model,
                        "mode": "multiuser",
                        "retrieved_chunks": relevant_chunks,
                        "sources": sources,
                        "cross_session_access": len(cross_session_sources) > 0,
                        "cross_session_sources": cross_session_sources,
                        "tokens_used": result.get("eval_count", 0),
                        "processing_time": result.get("eval_duration", 0) / 1000000
                    }
                }
        
        except httpx.HTTPError as e:
            raise Exception(f"Ollama API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Multi-user service error: {str(e)}")
    
    async def get_conversation(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])
    
    async def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    async def get_session_documents(self, session_id: str) -> List[Dict]:
        """Get documents for a session"""
        session_docs = self.session_documents.get(session_id, [])
        
        # Also include info about shared documents from other sessions
        accessible_shared = []
        for doc in self.shared_documents:
            if doc['session_id'] != session_id:
                accessible_shared.append({
                    **doc,
                    "access_type": "shared_cross_session"
                })
        
        return {
            "own_documents": session_docs,
            "accessible_shared": accessible_shared
        }