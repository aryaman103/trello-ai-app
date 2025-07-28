"""
Trello AI Agent - Advanced LangChain-based agent for Trello board management
Integrates GPT-4, structured tools, memory management, and confidence-based escalation
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# LangChain imports
try:
    from langchain.agents import create_openai_functions_agent, AgentExecutor
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, AIMessage
    from langchain.memory import ConversationBufferMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not available. Install with: pip install langchain langchain-openai")

# Local imports
from .tools import get_trello_tools, load_trello_data, save_trello_data
from .escalation import evaluate_and_escalate, escalation_system

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrelloMemoryManager:
    """Manages conversation memory and session tracking"""
    
    def __init__(self):
        self.sessions = {}
        self.session_file = "trello_sessions.json"
        self.load_sessions()
    
    def load_sessions(self):
        """Load session data from file"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    self.sessions = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load sessions: {e}")
            self.sessions = {}
    
    def save_sessions(self):
        """Save session data to file"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save sessions: {e}")
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get or create session"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "messages": [],
                "context": {},
                "stats": {
                    "total_interactions": 0,
                    "tools_used": [],
                    "escalations": 0,
                    "fallback_count": 0
                }
            }
            self.save_sessions()
        
        return self.sessions[session_id]
    
    def add_interaction(self, session_id: str, user_input: str, agent_response: str, 
                       tools_used: List[str], confidence_score: float):
        """Add interaction to session memory"""
        session = self.get_session(session_id)
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "agent_response": agent_response,
            "tools_used": tools_used,
            "confidence_score": confidence_score
        }
        
        session["messages"].append(interaction)
        session["stats"]["total_interactions"] += 1
        session["stats"]["tools_used"].extend(tools_used)
        
        # Keep only last 20 interactions to manage memory
        if len(session["messages"]) > 20:
            session["messages"] = session["messages"][-20:]
        
        self.save_sessions()
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> str:
        """Get formatted conversation history"""
        session = self.get_session(session_id)
        recent_messages = session["messages"][-limit:]
        
        history = []
        for msg in recent_messages:
            history.append(f"User: {msg['user_input']}")
            history.append(f"Assistant: {msg['agent_response']}")
        
        return "\n".join(history)
    
    def increment_fallback_count(self, session_id: str):
        """Increment fallback count for escalation tracking"""
        session = self.get_session(session_id)
        session["stats"]["fallback_count"] += 1
        self.save_sessions()
    
    def reset_fallback_count(self, session_id: str):
        """Reset fallback count after successful interaction"""
        session = self.get_session(session_id)
        session["stats"]["fallback_count"] = 0
        self.save_sessions()

class TrelloAIAgent:
    """Advanced Trello AI Agent with LangChain integration"""
    
    def __init__(self, openai_api_key: Optional[str] = None, confidence_threshold: float = 0.7):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.confidence_threshold = confidence_threshold
        self.agent_executor = None
        self.is_initialized = False
        self.memory_manager = TrelloMemoryManager()
        
        # Initialize Trello data
        load_trello_data()
        
        if LANGCHAIN_AVAILABLE and self.openai_api_key:
            self._initialize_langchain_agent()
        else:
            logger.warning("LangChain or OpenAI API key not available - using fallback mode")
    
    def _initialize_langchain_agent(self):
        """Initialize the LangChain agent with tools and memory"""
        try:
            # Initialize GPT-4 LLM
            llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                openai_api_key=self.openai_api_key,
                max_tokens=1000
            )
            
            # Get Trello tools
            tools = get_trello_tools()
            
            # Create system prompt
            system_prompt = """You are an advanced AI assistant specialized in Trello board management. 
You have access to powerful tools to help users create, organize, and manage their Trello boards effectively.

Your capabilities include:
- Creating boards, lists, and cards with intelligent suggestions
- Searching and organizing existing content
- Generating project-specific card suggestions based on user descriptions
- Understanding project management workflows and best practices

Guidelines for responses:
1. Be helpful, proactive, and specific in your suggestions
2. Use tools whenever possible to take concrete actions
3. When creating cards, make titles clear and add useful descriptions
4. Consider project management best practices in your suggestions
5. If you create multiple items, summarize what you've accomplished
6. Be conversational but professional

Current conversation context:
{chat_history}

Remember: Always aim to provide actionable help and use your tools to make actual changes to the user's Trello boards.
"""
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create agent
            agent = create_openai_functions_agent(llm, tools, prompt)
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=3,
                handle_parsing_errors=True,
                return_intermediate_steps=True
            )
            
            self.is_initialized = True
            logger.info("Trello AI Agent initialized successfully with LangChain")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain agent: {e}")
            self.is_initialized = False
    
    def chat(self, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process user input and generate response
        
        Args:
            user_input: User's message
            session_id: Session identifier (auto-generated if not provided)
            
        Returns:
            Dictionary containing response and metadata
        """
        if not session_id:
            session_id = f"session-{uuid.uuid4().hex[:8]}"
        
        start_time = datetime.now()
        
        try:
            # Get conversation history
            chat_history = self.memory_manager.get_conversation_history(session_id)
            
            if self.is_initialized and self.agent_executor:
                # Use LangChain agent
                response = self.agent_executor.invoke({
                    "input": user_input,
                    "chat_history": chat_history
                })
                
                agent_response = response.get("output", "I apologize, but I couldn't process your request.")
                intermediate_steps = response.get("intermediate_steps", [])
                
                # Extract tools used
                tools_used = []
                for step in intermediate_steps:
                    if len(step) >= 2 and hasattr(step[0], 'tool'):
                        tools_used.append(step[0].tool)
                
            else:
                # Fallback to simple responses
                agent_response = self._fallback_response(user_input)
                tools_used = []
                self.memory_manager.increment_fallback_count(session_id)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Get session stats for escalation context
            session = self.memory_manager.get_session(session_id)
            fallback_count = session["stats"]["fallback_count"]
            
            # Evaluate confidence and check for escalation
            escalation_result = evaluate_and_escalate(
                user_input=user_input,
                agent_response=agent_response,
                tools_used=tools_used,
                session_id=session_id,
                response_time=response_time,
                fallback_count=fallback_count
            )
            
            confidence_score = escalation_result["confidence_score"]
            escalation_decision = escalation_result["escalation"]
            
            # Store interaction in memory
            self.memory_manager.add_interaction(
                session_id, user_input, agent_response, tools_used, confidence_score
            )
            
            # Reset fallback count if we had a successful interaction
            if confidence_score >= self.confidence_threshold:
                self.memory_manager.reset_fallback_count(session_id)
            
            # Prepare response
            result = {
                "response": agent_response,
                "session_id": session_id,
                "confidence_score": confidence_score,
                "tools_used": tools_used,
                "response_time": response_time,
                "escalation": escalation_decision,
                "status": "success",
                "agent_type": "langchain" if self.is_initialized else "fallback"
            }
            
            # Add escalation message if needed
            if escalation_decision["should_escalate"]:
                result["escalation_message"] = escalation_result["escalation_message"]
                session["stats"]["escalations"] += 1
                self.memory_manager.save_sessions()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing chat: {e}")
            
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.",
                "session_id": session_id,
                "confidence_score": 0.0,
                "tools_used": [],
                "response_time": (datetime.now() - start_time).total_seconds(),
                "escalation": {"should_escalate": True, "reasons": ["System error"]},
                "status": "error",
                "error": str(e)
            }
    
    def _fallback_response(self, user_input: str) -> str:
        """Simple fallback responses when LangChain is not available"""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['create', 'make', 'new']):
            if 'board' in user_lower:
                return "I can help you create a new board! However, I need LangChain integration to perform actual board creation. Please provide your OpenAI API key and install required dependencies."
            elif 'card' in user_lower or 'task' in user_lower:
                return "I'd be happy to help create cards for your project! To use my full capabilities, please set up the backend with your OpenAI API key."
        
        elif any(word in user_lower for word in ['help', 'what', 'how']):
            return """I'm your Trello AI assistant! I can help you with:
            
• Creating boards, lists, and cards
• Generating project-specific task suggestions  
• Organizing and searching your boards
• Project management best practices

For full functionality, please ensure the backend is configured with your OpenAI API key."""
        
        else:
            return "I understand you'd like help with your Trello boards. For the best assistance, please ensure the backend is properly configured with LangChain and OpenAI integration."
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status information"""
        return {
            "langchain_available": LANGCHAIN_AVAILABLE,
            "openai_configured": bool(self.openai_api_key),
            "agent_initialized": self.is_initialized,
            "confidence_threshold": self.confidence_threshold,
            "agent_type": "langchain" if self.is_initialized else "fallback",
            "tools_available": len(get_trello_tools()),
            "escalation_stats": escalation_system.get_escalation_stats(),
            "active_sessions": len(self.memory_manager.sessions)
        }
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a specific session"""
        session = self.memory_manager.get_session(session_id)
        return {
            "session_id": session_id,
            "created_at": session["created_at"],
            "total_interactions": session["stats"]["total_interactions"],
            "tools_used_count": len(set(session["stats"]["tools_used"])),
            "escalations": session["stats"]["escalations"],
            "fallback_count": session["stats"]["fallback_count"],
            "recent_messages": len(session["messages"])
        }

# Global agent instance
trello_agent = TrelloAIAgent()

def get_trello_response(user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to get Trello AI response
    
    Args:
        user_input: User's message
        session_id: Optional session identifier
        
    Returns:
        Dictionary containing response and metadata
    """
    return trello_agent.chat(user_input, session_id)

if __name__ == "__main__":
    # Test the agent
    print("Testing Trello AI Agent...")
    print(f"Agent Status: {trello_agent.get_agent_status()}")
    
    # Test queries
    test_queries = [
        "Create a new board for my web development project",
        "Add some cards for a mobile app project in the 'To Do' list",
        "Help me organize my project tasks",
        "What boards do I have?",
        "Search for cards about testing"
    ]
    
    for query in test_queries:
        print(f"\nQ: {query}")
        result = get_trello_response(query, "test_session")
        print(f"A: {result['response']}")
        print(f"Confidence: {result['confidence_score']}")
        print(f"Tools Used: {result['tools_used']}")
        if result['escalation']['should_escalate']:
            print(f"⚠️ Escalation: {result['escalation']['reasons']}")