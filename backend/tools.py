"""
Trello AI Tools - LangChain-compatible functions for Trello operations
Implements structured tools for the AI agent to interact with Trello boards
"""

from langchain.tools import tool
from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime
import os

# In-memory storage for boards (in production, use a database)
TRELLO_DATA = {
    "boards": {},
    "lists": {},
    "cards": {}
}

def load_trello_data():
    """Load Trello data from file if it exists"""
    try:
        data_file = "trello_data.json"
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                global TRELLO_DATA
                TRELLO_DATA = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load Trello data: {e}")

def save_trello_data():
    """Save Trello data to file"""
    try:
        data_file = "trello_data.json"
        with open(data_file, 'w') as f:
            json.dump(TRELLO_DATA, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save Trello data: {e}")

# Initialize data
load_trello_data()

@tool
def create_board(title: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new Trello board
    
    Args:
        title: Board title
        description: Optional board description
    
    Returns:
        Dictionary containing board creation result
    """
    board_id = f"board-{uuid.uuid4().hex[:8]}"
    
    board = {
        "id": board_id,
        "title": title,
        "description": description,
        "lists": [],
        "created_at": datetime.now().isoformat(),
        "ai_created": True
    }
    
    TRELLO_DATA["boards"][board_id] = board
    save_trello_data()
    
    return {
        "success": True,
        "board_id": board_id,
        "title": title,
        "message": f"Board '{title}' created successfully"
    }

@tool
def create_list(board_id: str, title: str) -> Dict[str, Any]:
    """
    Create a new list in a board
    
    Args:
        board_id: ID of the board to add the list to
        title: List title
    
    Returns:
        Dictionary containing list creation result
    """
    if board_id not in TRELLO_DATA["boards"]:
        return {"success": False, "error": f"Board {board_id} not found"}
    
    list_id = f"list-{uuid.uuid4().hex[:8]}"
    
    list_data = {
        "id": list_id,
        "title": title,
        "board_id": board_id,
        "cards": [],
        "created_at": datetime.now().isoformat(),
        "ai_created": True
    }
    
    TRELLO_DATA["lists"][list_id] = list_data
    TRELLO_DATA["boards"][board_id]["lists"].append(list_id)
    save_trello_data()
    
    return {
        "success": True,
        "list_id": list_id,
        "title": title,
        "board_id": board_id,
        "message": f"List '{title}' created in board"
    }

@tool
def create_card(list_id: str, title: str, description: str = "") -> Dict[str, Any]:
    """
    Create a new card in a list
    
    Args:
        list_id: ID of the list to add the card to
        title: Card title
        description: Optional card description
    
    Returns:
        Dictionary containing card creation result
    """
    if list_id not in TRELLO_DATA["lists"]:
        return {"success": False, "error": f"List {list_id} not found"}
    
    card_id = f"card-{uuid.uuid4().hex[:8]}"
    
    card = {
        "id": card_id,
        "title": title,
        "description": description,
        "list_id": list_id,
        "created_at": datetime.now().isoformat(),
        "ai_suggested": True
    }
    
    TRELLO_DATA["cards"][card_id] = card
    TRELLO_DATA["lists"][list_id]["cards"].append(card_id)
    save_trello_data()
    
    return {
        "success": True,
        "card_id": card_id,
        "title": title,
        "list_id": list_id,
        "message": f"Card '{title}' created successfully"
    }

@tool
def get_boards() -> Dict[str, Any]:
    """
    Get all boards
    
    Returns:
        Dictionary containing all boards
    """
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
        "success": True,
        "boards": boards_list,
        "total_boards": len(boards_list)
    }

@tool
def get_board_details(board_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific board
    
    Args:
        board_id: ID of the board to retrieve
    
    Returns:
        Dictionary containing board details with lists and cards
    """
    if board_id not in TRELLO_DATA["boards"]:
        return {"success": False, "error": f"Board {board_id} not found"}
    
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
        "success": True,
        "board": {
            "id": board["id"],
            "title": board["title"],
            "description": board.get("description", ""),
            "lists": lists_with_cards,
            "created_at": board.get("created_at", ""),
            "ai_created": board.get("ai_created", False)
        }
    }

@tool
def suggest_cards_for_project(project_description: str, list_id: str) -> Dict[str, Any]:
    """
    Generate AI-suggested cards for a project based on description
    
    Args:
        project_description: Description of the project
        list_id: ID of the list to suggest cards for
    
    Returns:
        Dictionary containing suggested cards
    """
    if list_id not in TRELLO_DATA["lists"]:
        return {"success": False, "error": f"List {list_id} not found"}
    
    # AI-generated suggestions based on common project patterns
    project_lower = project_description.lower()
    suggestions = []
    
    # Web development suggestions
    if any(word in project_lower for word in ['website', 'web', 'frontend', 'backend', 'api']):
        suggestions.extend([
            {"title": "Set up project structure", "description": "Initialize repository and folder structure"},
            {"title": "Design user interface mockups", "description": "Create wireframes and design prototypes"},
            {"title": "Implement authentication system", "description": "Set up user login and registration"},
            {"title": "Create API endpoints", "description": "Develop backend API for data operations"},
            {"title": "Set up database", "description": "Design and implement database schema"},
            {"title": "Write unit tests", "description": "Create comprehensive test suite"},
            {"title": "Deploy to staging", "description": "Set up staging environment for testing"}
        ])
    
    # Mobile app suggestions
    elif any(word in project_lower for word in ['mobile', 'app', 'ios', 'android']):
        suggestions.extend([
            {"title": "Create app wireframes", "description": "Design user interface layouts"},
            {"title": "Set up development environment", "description": "Install SDKs and development tools"},
            {"title": "Implement core features", "description": "Build main app functionality"},
            {"title": "Test on devices", "description": "Test app on various devices and screen sizes"},
            {"title": "Prepare app store submission", "description": "Create app store listings and assets"}
        ])
    
    # Data/AI project suggestions
    elif any(word in project_lower for word in ['data', 'ai', 'machine learning', 'analysis']):
        suggestions.extend([
            {"title": "Data collection and cleaning", "description": "Gather and preprocess dataset"},
            {"title": "Exploratory data analysis", "description": "Analyze data patterns and insights"},
            {"title": "Feature engineering", "description": "Create relevant features for modeling"},
            {"title": "Model training and validation", "description": "Build and validate ML models"},
            {"title": "Create visualization dashboard", "description": "Build interactive data visualizations"}
        ])
    
    # Generic project suggestions
    else:
        suggestions.extend([
            {"title": "Project planning and research", "description": "Define requirements and research solutions"},
            {"title": "Create project timeline", "description": "Set milestones and deadlines"},
            {"title": "Set up development environment", "description": "Configure tools and workspace"},
            {"title": "Implement core functionality", "description": "Build main features"},
            {"title": "Testing and quality assurance", "description": "Test functionality and fix issues"},
            {"title": "Documentation", "description": "Write user and technical documentation"},
            {"title": "Deployment preparation", "description": "Prepare for production deployment"}
        ])
    
    # Limit to 5 suggestions
    suggestions = suggestions[:5]
    
    return {
        "success": True,
        "suggestions": suggestions,
        "project_description": project_description,
        "list_id": list_id,
        "message": f"Generated {len(suggestions)} card suggestions for your project"
    }

@tool
def search_cards(query: str) -> Dict[str, Any]:
    """
    Search for cards across all boards
    
    Args:
        query: Search query string
    
    Returns:
        Dictionary containing search results
    """
    query_lower = query.lower()
    matching_cards = []
    
    for card_id, card in TRELLO_DATA["cards"].items():
        title_match = query_lower in card["title"].lower()
        desc_match = query_lower in card.get("description", "").lower()
        
        if title_match or desc_match:
            # Get list and board info
            list_id = card["list_id"]
            list_info = TRELLO_DATA["lists"].get(list_id, {})
            board_id = list_info.get("board_id", "")
            board_info = TRELLO_DATA["boards"].get(board_id, {})
            
            matching_cards.append({
                "card_id": card["id"],
                "title": card["title"],
                "description": card.get("description", ""),
                "list_title": list_info.get("title", "Unknown List"),
                "board_title": board_info.get("title", "Unknown Board"),
                "created_at": card.get("created_at", "")
            })
    
    return {
        "success": True,
        "query": query,
        "results": matching_cards,
        "total_found": len(matching_cards)
    }

# Tool registry
TRELLO_TOOLS = [
    create_board,
    create_list,
    create_card,
    get_boards,
    get_board_details,
    suggest_cards_for_project,
    search_cards
]

def get_trello_tools():
    """Return list of Trello tools for agent registration"""
    return TRELLO_TOOLS