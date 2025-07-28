"""
FastAPI Backend for Trello AI
Provides REST API endpoints for the enhanced Trello AI with LangChain integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our agent
from .agent import get_trello_response, trello_agent
from .escalation import escalation_system
from .tools import TRELLO_DATA, save_trello_data

# Initialize FastAPI app
app = FastAPI(
    title="Trello AI API",
    description="Advanced AI assistant for Trello board management with LangChain integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
if os.path.exists("../index.html"):
    app.mount("/static", StaticFiles(directory=".."), name="static")

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    confidence_score: float
    tools_used: List[str]
    response_time: float
    escalation: Dict[str, Any]
    status: str
    agent_type: str
    escalation_message: Optional[str] = None

class FeedbackRequest(BaseModel):
    session_id: str
    user_query: str
    bot_response: str
    rating: int  # 1-5
    feedback_text: Optional[str] = None
    tools_used: List[str] = []
    response_time: float = 0.0
    escalation_triggered: bool = False

class BoardData(BaseModel):
    boards: List[Dict[str, Any]]

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint - serve the main page"""
    return {"message": "Trello AI API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    agent_status = trello_agent.get_agent_status()
    return {
        "status": "healthy",
        "agent_initialized": agent_status["agent_initialized"],
        "langchain_available": agent_status["langchain_available"],
        "openai_configured": agent_status["openai_configured"]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the Trello AI agent
    
    Args:
        request: ChatRequest with message and optional session_id
        
    Returns:
        ChatResponse with agent's response and metadata
    """
    try:
        result = get_trello_response(request.message, request.session_id)
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            confidence_score=result["confidence_score"],
            tools_used=result["tools_used"],
            response_time=result["response_time"],
            escalation=result["escalation"],
            status=result["status"],
            agent_type=result["agent_type"],
            escalation_message=result.get("escalation_message")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for a chat interaction
    
    Args:
        request: FeedbackRequest with rating and feedback details
        
    Returns:
        Success confirmation
    """
    try:
        # Store feedback (in production, use a proper database)
        feedback_data = {
            "session_id": request.session_id,
            "user_query": request.user_query,
            "bot_response": request.bot_response,
            "rating": request.rating,
            "feedback_text": request.feedback_text,
            "tools_used": request.tools_used,
            "response_time": request.response_time,
            "escalation_triggered": request.escalation_triggered,
            "timestamp": "now"  # Would use proper timestamp in production
        }
        
        # TODO: Store in database
        
        return {
            "status": "success",
            "message": "Feedback submitted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@app.get("/boards")
async def get_all_boards():
    """
    Get all Trello boards
    
    Returns:
        List of all boards with basic information
    """
    try:
        boards_list = []
        for board_id, board in TRELLO_DATA["boards"].items():
            board_info = {
                "id": board["id"],
                "title": board["title"],
                "description": board.get("description", ""),
                "lists_count": len(board["lists"]),
                "created_at": board.get("created_at", ""),
                "ai_created": board.get("ai_created", False)
            }
            boards_list.append(board_info)
        
        return {
            "boards": boards_list,
            "total_boards": len(boards_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching boards: {str(e)}")

@app.get("/boards/{board_id}")
async def get_board_details(board_id: str):
    """
    Get detailed information about a specific board
    
    Args:
        board_id: ID of the board to retrieve
        
    Returns:
        Detailed board information with lists and cards
    """
    try:
        if board_id not in TRELLO_DATA["boards"]:
            raise HTTPException(status_code=404, detail=f"Board {board_id} not found")
        
        board = TRELLO_DATA["boards"][board_id]
        
        # Get lists with cards
        lists_with_cards = []
        for list_id in board["lists"]:
            if list_id in TRELLO_DATA["lists"]:
                list_data = TRELLO_DATA["lists"][list_id]
                
                # Get cards for this list
                cards = []
                for card_id in list_data["cards"]:
                    if card_id in TRELLO_DATA["cards"]:
                        cards.append(TRELLO_DATA["cards"][card_id])
                
                list_with_cards = {
                    "id": list_data["id"],
                    "title": list_data["title"],
                    "cards": cards,
                    "cards_count": len(cards)
                }
                lists_with_cards.append(list_with_cards)
        
        return {
            "board": {
                "id": board["id"],
                "title": board["title"],
                "description": board.get("description", ""),
                "lists": lists_with_cards,
                "created_at": board.get("created_at", ""),
                "ai_created": board.get("ai_created", False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching board details: {str(e)}")

@app.get("/analytics")
async def get_analytics():
    """
    Get analytics about agent performance and usage
    
    Returns:
        Analytics data including escalation stats, agent performance, etc.
    """
    try:
        agent_status = trello_agent.get_agent_status()
        escalation_stats = escalation_system.get_escalation_stats()
        
        # Board statistics
        total_boards = len(TRELLO_DATA["boards"])
        total_lists = len(TRELLO_DATA["lists"])
        total_cards = len(TRELLO_DATA["cards"])
        ai_created_boards = sum(1 for board in TRELLO_DATA["boards"].values() 
                               if board.get("ai_created", False))
        ai_suggested_cards = sum(1 for card in TRELLO_DATA["cards"].values() 
                                if card.get("ai_suggested", False))
        
        return {
            "agent_status": agent_status,
            "escalation_stats": escalation_stats,
            "board_stats": {
                "total_boards": total_boards,
                "total_lists": total_lists,
                "total_cards": total_cards,
                "ai_created_boards": ai_created_boards,
                "ai_suggested_cards": ai_suggested_cards,
                "ai_usage_rate": round((ai_created_boards + ai_suggested_cards) / max(total_boards + total_cards, 1) * 100, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")

@app.get("/session/{session_id}/stats")
async def get_session_stats(session_id: str):
    """
    Get statistics for a specific session
    
    Args:
        session_id: ID of the session
        
    Returns:
        Session statistics
    """
    try:
        stats = trello_agent.get_session_stats(session_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session stats: {str(e)}")

@app.post("/admin/reset-data")
async def reset_data():
    """
    Admin endpoint to reset all Trello data (use with caution)
    """
    try:
        global TRELLO_DATA
        TRELLO_DATA = {
            "boards": {},
            "lists": {},
            "cards": {}
        }
        save_trello_data()
        
        return {
            "status": "success",
            "message": "All Trello data has been reset"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting data: {str(e)}")

@app.get("/admin/export-data")
async def export_data():
    """
    Admin endpoint to export all data
    """
    try:
        return {
            "trello_data": TRELLO_DATA,
            "agent_status": trello_agent.get_agent_status(),
            "escalation_stats": escalation_system.get_escalation_stats()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")

# Background task for data persistence
async def periodic_save():
    """Periodically save data to ensure persistence"""
    save_trello_data()

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"Starting Trello AI API server...")
    print(f"Agent Status: {trello_agent.get_agent_status()}")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )