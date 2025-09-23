from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import json
import os
from typing import List, Optional
import uuid
from datetime import datetime
from fastapi.responses import StreamingResponse
import asyncio


from models import ChatRequest, ChatResponse, Mode, ModeInfo
from services.llm_service import LLMService
from services.guardrails_service import GuardrailsService
from services.rag_service import RAGService
from services.multiuser_service import MultiUserService

app = FastAPI(title="AI Red Teaming Playground", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()
guardrails_service = GuardrailsService()
rag_service = RAGService()
multiuser_service = MultiUserService()

# Available modes with descriptions and architecture info
MODES = {
    Mode.SIMPLE: ModeInfo(
        name="Simple LLM",
        description="Direct interaction with phi3:mini for prompt injection testing",
        architecture="User Input → phi3:mini → Response",
        details="Test basic prompt injections, jailbreaks, and adversarial inputs directly against the base model."
    ),
    Mode.GUARDRAILS: ModeInfo(
        name="Guardrails Testing",
        description="LLM with safety guardrails that can be tested for bypass attempts",
        architecture="User Input → Safety Filter → phi3:mini → Response Filter → Response",
        details="Test guardrail bypass techniques including role-playing, encoding, and social engineering."
    ),
    Mode.RAG: ModeInfo(
        name="RAG Setup",
        description="Retrieval-Augmented Generation with user-uploaded documents",
        architecture="User Input → Vector Search → Document Chunks → phi3:mini + Context → Response",
        details="Test information extraction, context manipulation, and document-based prompt injection."
    ),
    Mode.MULTIUSER: ModeInfo(
        name="Multi-User Chat",
        description="Cross-session document access and sharing capabilities",
        architecture="User Input → Shared Vector Store → Document Retrieval → phi3:mini → Response",
        details="Test cross-user information leakage and session isolation bypasses."
    )
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Ollama connection
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                return {"status": "healthy", "ollama": "connected"}
            else:
                return {"status": "degraded", "ollama": "disconnected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/modes")
async def get_modes():
    """Get available testing modes"""
    return {"modes": MODES}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint that routes to different modes"""
    try:
        if request.mode not in MODES:
            raise HTTPException(status_code=400, detail="Invalid mode")
        
        # Route to appropriate service based on mode
        if request.mode == Mode.SIMPLE:
            response = await llm_service.chat(request.message, request.conversation_id)
        elif request.mode == Mode.GUARDRAILS:
            response = await guardrails_service.chat(request.message, request.conversation_id)
        elif request.mode == Mode.RAG:
            response = await rag_service.chat(request.message, request.conversation_id, request.session_id)
        elif request.mode == Mode.MULTIUSER:
            response = await multiuser_service.chat(request.message, request.conversation_id, request.session_id)
        else:
            raise HTTPException(status_code=400, detail="Mode not implemented")
        
        return ChatResponse(
            response=response["content"],
            conversation_id=response["conversation_id"],
            mode=request.mode,
            timestamp=datetime.now(),
            metadata=response.get("metadata", {})
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    session_id: str = Form(...),
    mode: str = Form(default="rag")
):
    """Upload documents for RAG and Multi-user modes"""
    try:
        uploaded_files = []
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            # Save file
            file_id = str(uuid.uuid4())
            file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
            
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Process based on mode
            if mode == "rag":
                await rag_service.add_document(file_path, session_id)
            elif mode == "multiuser":
                await multiuser_service.add_document(file_path, session_id)
            
            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "size": len(content)
            })
        
        return {"uploaded_files": uploaded_files, "session_id": session_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, mode: str):
    """Get conversation history"""
    try:
        if mode == "simple":
            history = await llm_service.get_conversation(conversation_id)
        elif mode == "guardrails":
            history = await guardrails_service.get_conversation(conversation_id)
        elif mode == "rag":
            history = await rag_service.get_conversation(conversation_id)
        elif mode == "multiuser":
            history = await multiuser_service.get_conversation(conversation_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")
        
        return {"conversation_id": conversation_id, "history": history}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str, mode: str):
    """Clear conversation history"""
    try:
        if mode == "simple":
            await llm_service.clear_conversation(conversation_id)
        elif mode == "guardrails":
            await guardrails_service.clear_conversation(conversation_id)
        elif mode == "rag":
            await rag_service.clear_conversation(conversation_id)
        elif mode == "multiuser":
            await multiuser_service.clear_conversation(conversation_id)
        
        return {"message": "Conversation cleared"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/documents")
async def get_session_documents(session_id: str, mode: str = "rag"):
    """Get documents for a session"""
    try:
        if mode == "rag":
            docs = await rag_service.get_session_documents(session_id)
        elif mode == "multiuser":
            docs = await multiuser_service.get_session_documents(session_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid mode for document retrieval")
        
        return {"session_id": session_id, "documents": docs}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_attempt(request: dict):
    """Analyze adversarial attempt (stretch goal)"""
    try:
        # This is a placeholder for analysis functionality
        analysis = {
            "attempt_type": "unknown",
            "success_probability": 0.0,
            "risk_level": "low",
            "detected_techniques": [],
            "recommendations": []
        }
        
        return {"analysis": analysis}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    