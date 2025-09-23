import httpx
import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime

class LLMService:
    def __init__(self):
        self.base_url = "http://localhost:11434/api/chat"
        self.model = "phi3:mini"
        self.conversations: Dict[str, List[Dict]] = {}
    
    async def chat(self, message: str, conversation_id: Optional[str] = None) -> Dict:
        """Simple LLM chat without any filtering"""
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        
        # Get or create conversation
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        conversation = self.conversations[conversation_id]
        
        # Add user message to conversation
        conversation.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now()
        })
        
        # Prepare messages for Ollama (only role and content)
        ollama_messages = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in conversation
        ]
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_url,
                    json={
                        "model": self.model,
                        "messages": ollama_messages,
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
                    "timestamp": datetime.now()
                })
                
                return {
                    "content": assistant_response,
                    "conversation_id": conversation_id,
                    "metadata": {
                        "model": self.model,
                        "mode": "simple",
                        "tokens_used": result.get("eval_count", 0),
                        "processing_time": result.get("eval_duration", 0) / 1000000  # Convert to ms
                    }
                }
        
        except httpx.HTTPError as e:
            raise Exception(f"Ollama API error: {str(e)}")
        except Exception as e:
            raise Exception(f"LLM service error: {str(e)}")
    
    async def get_conversation(self, conversation_id: str) -> List[Dict]:
        """Get conversation history"""
        return self.conversations.get(conversation_id, [])
    
    async def clear_conversation(self, conversation_id: str):
        """Clear conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
    
    def get_system_prompt(self) -> str:
        """Get the system prompt (for red teaming analysis)"""
        return "You are a helpful AI assistant."
    
