from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Dict, List, Any
from datetime import datetime

class Mode(str, Enum):
    SIMPLE = "simple"
    GUARDRAILS = "guardrails"  
    RAG = "rag"
    MULTIUSER = "multiuser"

class ChatRequest(BaseModel):
    message: str
    mode: Mode
    conversation_id: Optional[str] = None
    session_id: Optional[str] = None
    system_prompt: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    mode: Mode
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = {}

class ModeInfo(BaseModel):
    name: str
    description: str
    architecture: str
    details: str

class ConversationMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = {}

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    upload_time: datetime
    session_id: str
    size: int
    status: str  # "processing", "ready", "error"

class AnalysisResult(BaseModel):
    attempt_type: str
    success_probability: float
    risk_level: str
    detected_techniques: List[str]
    recommendations: List[str]
    confidence: float

class GuardrailResult(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    filtered_content: Optional[str] = None
    risk_score: float = 0.0

class RAGResult(BaseModel):
    response: str
    retrieved_chunks: List[Dict[str, Any]]
    relevance_scores: List[float]
    sources: List[str]