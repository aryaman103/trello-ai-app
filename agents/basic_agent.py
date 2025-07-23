"""
Basic HR Agent with LangChain Integration
Main agent implementation for HR chatbot functionality
"""

import os
import logging
from typing import Dict, Any, List, Optional
import json

# Import our custom modules
from .tools import get_tools_list
from memory.memory import hr_memory_manager
from data_ingest.ingest import hr_knowledge_base, create_knowledge_base_tool

try:
    from langchain.agents import create_openai_functions_agent, AgentExecutor
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not available. Install with: pip install langchain langchain-openai")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleHRBot:
    """
    Simple HR bot implementation without LangChain dependencies
    """
    
    def __init__(self):
        self.tools_map = {
            'leave_balance': self._get_leave_balance,
            'submit_leave': self._submit_leave_request,
            'policy_lookup': self._lookup_policy,
            'escalate': self._escalate_to_hr,
            'calendar': self._calendar_query,
            'directory': self._employee_directory
        }
    
    def _get_leave_balance(self, user_id: str = "emp_001") -> str:
        """Get leave balance for user"""
        from agents.tools import get_leave_balance
        result = get_leave_balance(user_id)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Leave Balance for {result['employee_name']}: {json.dumps(result['leave_balance'], indent=2)}"
    
    def _submit_leave_request(self, user_id: str, leave_type: str, start_date: str, end_date: str, reason: str) -> str:
        """Submit leave request"""
        from agents.tools import submit_leave_request
        result = submit_leave_request(user_id, leave_type, start_date, end_date, reason)
        if "error" in result:
            return f"Error: {result['error']}"
        return f"Leave request submitted successfully. Request ID: {result['request_id']}"
    
    def _lookup_policy(self, topic: str) -> str:
        """Look up HR policy"""
        from agents.tools import lookup_policy
        result = lookup_policy(topic)
        if "policies" in result:
            policies_text = "\n".join([f"{key}: {value}" for key, value in result["policies"].items()])
            return f"Policy information for '{topic}':\n{policies_text}"
        return result.get("message", "No policy information found")
    
    def _escalate_to_hr(self, user_id: str, issue_type: str, description: str) -> str:
        """Escalate issue to HR"""
        from agents.tools import escalate_to_hr
        result = escalate_to_hr(user_id, issue_type, description)
        return f"Issue escalated. Ticket ID: {result['ticket_id']}. {result['next_steps']}"
    
    def _calendar_query(self, query: str) -> str:
        """Query calendar information"""
        from agents.tools import calendar_api
        result = calendar_api(query)
        if "upcoming_holidays" in result:
            holidays = "\n".join([f"- {h['name']}: {h['date']}" for h in result["upcoming_holidays"]])
            return f"Upcoming company holidays:\n{holidays}"
        return result.get("message", "Calendar information not available")
    
    def _employee_directory(self, search_term: str = "") -> str:
        """Search employee directory"""
        from agents.tools import get_employee_directory
        result = get_employee_directory(search_term)
        if "departments" in result:
            dept_info = "\n".join([f"{dept}: {', '.join(employees)}" for dept, employees in result["departments"].items()])
            return f"Employee Directory:\n{dept_info}\nTotal employees: {result['total_employees']}"
        elif "results" in result:
            if result["results"]:
                emp_info = "\n".join([f"- {emp['name']} ({emp['department']}) - Manager: {emp['manager']}" for emp in result["results"]])
                return f"Search results for '{search_term}':\n{emp_info}"
            else:
                return f"No employees found matching '{search_term}'"
        return "Directory information not available"
    
    def chat(self, user_input: str, user_id: str = "default_user") -> str:
        """
        Simple chat interface with pattern matching
        """
        user_input_lower = user_input.lower()
        
        # Check for specific HR queries
        if any(word in user_input_lower for word in ['leave', 'vacation', 'balance', 'days off']):
            if 'balance' in user_input_lower or 'how many' in user_input_lower:
                return self._get_leave_balance()
            elif 'request' in user_input_lower or 'submit' in user_input_lower:
                return "To submit a leave request, please provide: leave type, start date, end date, and reason. Example: 'Submit vacation leave from 2024-07-01 to 2024-07-05 for family vacation'"
        
        elif any(word in user_input_lower for word in ['policy', 'policies', 'rule', 'procedure']):
            # Extract topic from input
            for word in ['vacation', 'sick', 'remote', 'holiday', 'expense']:
                if word in user_input_lower:
                    return self._lookup_policy(word)
            return self._lookup_policy("general")
        
        elif any(word in user_input_lower for word in ['holiday', 'holidays', 'calendar']):
            return self._calendar_query(user_input)
        
        elif any(word in user_input_lower for word in ['employee', 'directory', 'contact', 'find']):
            # Extract search term
            search_words = user_input.split()
            search_term = " ".join(search_words[1:]) if len(search_words) > 1 else ""
            return self._employee_directory(search_term)
        
        elif any(word in user_input_lower for word in ['help', 'escalate', 'issue', 'problem']):
            return self._escalate_to_hr("emp_001", "question", user_input)
        
        else:
            # Default response with available options
            return """I'm your HR assistant! I can help you with:
            
• Leave balance and vacation requests
• HR policies and procedures  
• Company holidays and calendar
• Employee directory searches
• Escalating issues to HR team

What would you like to know about?"""

class HRAgent:
    """
    Advanced HR Agent with LangChain integration
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.agent_executor = None
        self.is_initialized = False
        self.simple_bot = SimpleHRBot()  # Fallback bot
        
        if LANGCHAIN_AVAILABLE and self.openai_api_key:
            self._initialize_langchain_agent()
        else:
            logger.warning("Using simple bot fallback - LangChain or OpenAI API key not available")
    
    def _initialize_langchain_agent(self):
        """Initialize the LangChain agent with tools"""
        try:
            # Initialize LLM
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                openai_api_key=self.openai_api_key
            )
            
            # Get tools
            tools = get_tools_list()
            
            # Add knowledge base tool if available
            try:
                kb_tool = create_knowledge_base_tool()
                tools.append(kb_tool)
                logger.info("Added knowledge base tool to agent")
            except Exception as e:
                logger.warning(f"Knowledge base tool not available: {e}")
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful HR assistant. You have access to various HR tools and a knowledge base.
                
Your role is to:
- Help employees with leave requests and balance inquiries
- Provide information about HR policies and procedures
- Assist with calendar and holiday questions
- Help with employee directory searches
- Escalate complex issues to the HR team when needed

Always be professional, helpful, and accurate. When using tools, explain what you're doing.
If you cannot find specific information, offer to escalate to the HR team.

Current conversation context:
{chat_history}
                """),
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
                handle_parsing_errors=True
            )
            
            self.is_initialized = True
            logger.info("HR Agent initialized successfully with LangChain")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain agent: {e}")
            self.is_initialized = False
    
    def chat(self, user_input: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Chat with the HR agent
        
        Args:
            user_input: User's message
            user_id: Unique identifier for the user session
            
        Returns:
            Dictionary containing response and metadata
        """
        logger.info(f"Processing message from user {user_id}: {user_input}")
        
        # Get conversation history
        chat_history = hr_memory_manager.get_conversation_history(user_id)
        
        try:
            if self.is_initialized and self.agent_executor:
                # Use LangChain agent
                response = self.agent_executor.invoke({
                    "input": user_input,
                    "chat_history": chat_history
                })
                
                bot_response = response.get("output", "I apologize, but I couldn't process your request.")
                
            else:
                # Use simple bot fallback
                bot_response = self.simple_bot.chat(user_input, user_id)
            
            # Store the interaction in memory
            hr_memory_manager.add_interaction(user_id, user_input, bot_response)
            
            return {
                "response": bot_response,
                "user_id": user_id,
                "status": "success",
                "agent_type": "langchain" if self.is_initialized else "simple"
            }
            
        except Exception as e:
            logger.error(f"Error processing chat: {e}")
            
            # Fallback to simple bot
            try:
                bot_response = self.simple_bot.chat(user_input, user_id)
                hr_memory_manager.add_interaction(user_id, user_input, bot_response)
                
                return {
                    "response": bot_response,
                    "user_id": user_id,
                    "status": "success",
                    "agent_type": "simple_fallback",
                    "error": str(e)
                }
            except Exception as fallback_error:
                return {
                    "response": "I apologize, but I'm experiencing technical difficulties. Please try again later or contact HR directly.",
                    "user_id": user_id,
                    "status": "error",
                    "error": str(fallback_error)
                }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status information about the agent
        
        Returns:
            Dictionary with agent status information
        """
        return {
            "langchain_available": LANGCHAIN_AVAILABLE,
            "openai_configured": bool(self.openai_api_key),
            "agent_initialized": self.is_initialized,
            "agent_type": "langchain" if self.is_initialized else "simple",
            "memory_stats": hr_memory_manager.get_memory_stats()
        }

# Global HR agent instance
hr_agent = HRAgent()

def get_hr_response(user_input: str, user_id: str = "default_user") -> Dict[str, Any]:
    """
    Convenience function to get HR response
    
    Args:
        user_input: User's message
        user_id: User session identifier
        
    Returns:
        Dictionary containing response and metadata
    """
    return hr_agent.chat(user_input, user_id)

if __name__ == "__main__":
    # Test the HR agent
    print("Testing HR Agent...")
    
    # Test queries
    test_queries = [
        "What's my leave balance?",
        "How do I request vacation time?",
        "What are the company holidays this year?",
        "What's the remote work policy?",
        "Can you help me find John Doe's contact info?"
    ]
    
    for query in test_queries:
        print(f"\nQ: {query}")
        result = get_hr_response(query, "test_user")
        print(f"A: {result['response']}")
        print(f"Agent Type: {result['agent_type']}")
    
    # Print agent status
    print(f"\nAgent Status: {hr_agent.get_agent_status()}")