"""
FastAPI endpoint for HR Bot functionality
Provides REST API for HR chat interactions
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenv not available. Install with: pip install python-dotenv")
    pass

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not available. Install with: pip install fastapi uvicorn")

# Import HR agent
try:
    from agents.basic_agent import get_hr_response, hr_agent
    from memory.memory import hr_memory_manager
    from data_ingest.ingest import initialize_knowledge_base
    HR_MODULES_AVAILABLE = True
except ImportError as e:
    HR_MODULES_AVAILABLE = False
    print(f"HR modules not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str
    timestamp: str
    agent_type: str
    status: str

class LeaveRequest(BaseModel):
    user_id: str
    leave_type: str
    start_date: str
    end_date: str
    reason: str

class PolicyQuery(BaseModel):
    topic: str

class HealthResponse(BaseModel):
    status: str
    agent_initialized: bool
    components: Dict[str, str]
    timestamp: str

# Initialize FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="HR Bot API",
        description="REST API for HR chatbot functionality",
        version="1.0.0"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize components on startup"""
        logger.info("Starting HR Bot API...")
        
        if HR_MODULES_AVAILABLE:
            # Initialize knowledge base
            try:
                success = initialize_knowledge_base()
                if success:
                    logger.info("✓ Knowledge base initialized")
                else:
                    logger.warning("✗ Knowledge base initialization failed")
            except Exception as e:
                logger.error(f"✗ Knowledge base error: {e}")
        
        logger.info("HR Bot API started successfully")
    
    @app.get("/", response_model=Dict[str, str])
    async def root():
        """Root endpoint with API information"""
        return {
            "message": "HR Bot API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint"""
        components = {
            "fastapi": "available" if FASTAPI_AVAILABLE else "unavailable",
            "hr_modules": "available" if HR_MODULES_AVAILABLE else "unavailable"
        }
        
        agent_initialized = False
        if HR_MODULES_AVAILABLE:
            try:
                status = hr_agent.get_agent_status()
                agent_initialized = status.get("agent_initialized", False)
                components.update({
                    "langchain": "available" if status.get("langchain_available") else "unavailable",
                    "openai": "configured" if status.get("openai_configured") else "not_configured",
                    "agent_type": status.get("agent_type", "unknown")
                })
            except Exception as e:
                components["agent_error"] = str(e)
        
        return HealthResponse(
            status="healthy" if HR_MODULES_AVAILABLE else "degraded",
            agent_initialized=agent_initialized,
            components=components,
            timestamp=datetime.now().isoformat()
        )
    
    @app.post("/ai-chat")
    async def chat_with_ai_assistant(request: dict):
        """
        Chat with the AI assistant powered by ChatGPT 4o for task management
        
        Args:
            request: Dictionary containing message and context
            
        Returns:
            AI response for task management queries
        """
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="AI assistant not available"
            )
        
        try:
            from langchain_openai import ChatOpenAI
            
            # Initialize ChatGPT 4o for task management
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.1,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            user_message = request.get("message", "")
            context = request.get("context", "general")
            
            # Create task management prompt
            system_prompt = """You are an intelligent task management assistant integrated into a Trello-like application. 
Your role is to help users organize tasks, improve productivity, and manage their projects effectively.

Key capabilities:
- Analyze user requests for task creation, organization, and management
- Provide intelligent suggestions for task optimization
- Help with project planning and workflow improvements
- Suggest task breakdowns and prioritization

If the user asks you to create a task, respond with a JSON-like structure:
{"action": "create_task", "task_name": "extracted task name", "response": "your response"}

Otherwise, provide helpful task management advice and suggestions.
Be concise, actionable, and focused on productivity improvements."""

            # Generate response
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = llm.invoke(messages)
            ai_response = response.content
            
            # Check if response suggests creating a task
            if "create_task" in ai_response.lower() and "{" in ai_response:
                try:
                    import json
                    # Try to extract JSON-like response
                    json_start = ai_response.find("{")
                    json_end = ai_response.rfind("}") + 1
                    if json_start != -1 and json_end != -1:
                        json_part = ai_response[json_start:json_end]
                        parsed = json.loads(json_part)
                        return parsed
                except:
                    pass
            
            return {"response": ai_response}
            
        except Exception as e:
            logger.error(f"AI assistant error: {e}")
            raise HTTPException(
                status_code=500,
                detail="AI assistant temporarily unavailable"
            )

    @app.post("/chat", response_model=ChatResponse)
    async def chat_with_hr_bot(request: ChatRequest):
        """
        Chat with the HR bot
        
        Args:
            request: Chat request containing message and optional user/session IDs
            
        Returns:
            Chat response from the HR bot
        """
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="HR bot modules not available"
            )
        
        # Generate IDs if not provided
        user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
        
        try:
            # Get response from HR agent
            result = get_hr_response(request.message, user_id)
            
            return ChatResponse(
                response=result["response"],
                user_id=result["user_id"],
                session_id=session_id,
                timestamp=datetime.now().isoformat(),
                agent_type=result.get("agent_type", "unknown"),
                status=result.get("status", "success")
            )
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Chat processing failed: {str(e)}"
            )
    
    @app.post("/leave/balance")
    async def get_leave_balance(user_id: str = "emp_001"):
        """Get leave balance for a user"""
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="HR modules not available")
        
        try:
            from agents.tools import get_leave_balance
            result = get_leave_balance(user_id)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/leave/request")
    async def submit_leave_request(request: LeaveRequest):
        """Submit a leave request"""
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="HR modules not available")
        
        try:
            from agents.tools import submit_leave_request
            result = submit_leave_request(
                request.user_id,
                request.leave_type,
                request.start_date,
                request.end_date,
                request.reason
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/policy/lookup")
    async def lookup_policy(request: PolicyQuery):
        """Look up HR policy information"""
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="HR modules not available")
        
        try:
            from agents.tools import lookup_policy
            result = lookup_policy(request.topic)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/calendar/holidays")
    async def get_holidays():
        """Get company holiday information"""
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="HR modules not available")
        
        try:
            from agents.tools import calendar_api
            result = calendar_api("holidays")
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/directory")
    async def search_directory(search_term: str = ""):
        """Search employee directory"""
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="HR modules not available")
        
        try:
            from agents.tools import get_employee_directory
            result = get_employee_directory(search_term)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/memory/stats")
    async def get_memory_stats():
        """Get memory usage statistics"""
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="HR modules not available")
        
        try:
            stats = hr_memory_manager.get_memory_stats()
            return stats
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/memory/{user_id}")
    async def clear_user_memory(user_id: str):
        """Clear memory for a specific user"""
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="HR modules not available")
        
        try:
            hr_memory_manager.clear_user_memory(user_id)
            return {"message": f"Memory cleared for user {user_id}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/agent/status")
    async def get_agent_status():
        """Get detailed agent status information"""
        if not HR_MODULES_AVAILABLE:
            raise HTTPException(status_code=503, detail="HR modules not available")
        
        try:
            status = hr_agent.get_agent_status()
            return status
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

else:
    # Fallback if FastAPI not available
    class MockApp:
        def __init__(self):
            print("FastAPI not available. API functionality disabled.")
        
        def run(self, host="localhost", port=8000):
            print(f"Cannot start API server - FastAPI not installed")
            print("Install with: pip install fastapi uvicorn")
    
    app = MockApp()

def run_server(host: str = "localhost", port: int = 8000, reload: bool = True):
    """
    Run the HR Bot API server
    
    Args:
        host: Host to bind to
        port: Port to listen on
        reload: Enable auto-reload for development
    """
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available. Cannot start server.")
        print("Install with: pip install fastapi uvicorn")
        return
    
    if not HR_MODULES_AVAILABLE:
        print("Warning: HR modules not fully available. Some features may not work.")
    
    print(f"Starting HR Bot API server on http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "hr_api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    # Run the server
    run_server()