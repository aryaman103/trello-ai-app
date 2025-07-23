"""
Memory Management for HR Bot
Provides different memory strategies for maintaining conversation context
"""

from typing import Any, Dict, List, Optional
import logging

try:
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain not available. Install with: pip install langchain")

# Configure logging
logger = logging.getLogger(__name__)

class SimpleMemory:
    """
    Simple memory implementation without LangChain dependencies
    """
    
    def __init__(self, max_messages: int = 20):
        self.messages = []
        self.max_messages = max_messages
    
    def add_message(self, role: str, content: str):
        """Add a message to memory"""
        self.messages.append({"role": role, "content": content})
        
        # Keep only the last max_messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get all messages"""
        return self.messages.copy()
    
    def clear(self):
        """Clear all messages"""
        self.messages.clear()
    
    def get_context_string(self) -> str:
        """Get conversation history as a formatted string"""
        if not self.messages:
            return "No previous conversation."
        
        context_parts = []
        for msg in self.messages[-10:]:  # Last 10 messages for context
            role = "Human" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)

def get_buffer_memory(memory_key: str = "chat_history") -> Any:
    """
    Get a conversation buffer memory instance
    
    Args:
        memory_key: Key to use for storing memory
        
    Returns:
        ConversationBufferMemory instance or SimpleMemory fallback
    """
    if LANGCHAIN_AVAILABLE:
        try:
            memory = ConversationBufferMemory(
                memory_key=memory_key,
                return_messages=True,
                input_key="input",
                output_key="output"
            )
            logger.info("Using LangChain ConversationBufferMemory")
            return memory
        except Exception as e:
            logger.warning(f"Failed to create ConversationBufferMemory: {e}")
    
    # Fallback to simple memory
    logger.info("Using SimpleMemory fallback")
    return SimpleMemory()

def get_summary_memory(llm, memory_key: str = "chat_history", max_token_limit: int = 2000) -> Any:
    """
    Get a conversation summary memory instance
    
    Args:
        llm: Language model for summarization
        memory_key: Key to use for storing memory
        max_token_limit: Maximum tokens before summarization
        
    Returns:
        ConversationSummaryMemory instance or SimpleMemory fallback
    """
    if LANGCHAIN_AVAILABLE and llm:
        try:
            memory = ConversationSummaryMemory(
                llm=llm,
                memory_key=memory_key,
                return_messages=True,
                max_token_limit=max_token_limit,
                input_key="input",
                output_key="output"
            )
            logger.info("Using LangChain ConversationSummaryMemory")
            return memory
        except Exception as e:
            logger.warning(f"Failed to create ConversationSummaryMemory: {e}")
    
    # Fallback to simple memory
    logger.info("Using SimpleMemory fallback for summary memory")
    return SimpleMemory(max_messages=10)  # Smaller buffer for summary memory

class HRBotMemoryManager:
    """
    Enhanced memory manager for HR Bot with conversation context
    """
    
    def __init__(self, memory_type: str = "buffer", llm=None):
        self.memory_type = memory_type
        self.llm = llm
        self.user_sessions = {}  # Store memory per user session
        
    def get_memory_for_user(self, user_id: str) -> Any:
        """
        Get or create memory instance for a specific user
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            Memory instance for the user
        """
        if user_id not in self.user_sessions:
            if self.memory_type == "summary":
                self.user_sessions[user_id] = get_summary_memory(self.llm)
            else:
                self.user_sessions[user_id] = get_buffer_memory()
        
        return self.user_sessions[user_id]
    
    def add_interaction(self, user_id: str, user_input: str, bot_response: str):
        """
        Add an interaction to user's memory
        
        Args:
            user_id: User identifier
            user_input: User's input message
            bot_response: Bot's response message
        """
        memory = self.get_memory_for_user(user_id)
        
        if isinstance(memory, SimpleMemory):
            memory.add_message("user", user_input)
            memory.add_message("assistant", bot_response)
        else:
            # LangChain memory
            try:
                if hasattr(memory, 'save_context'):
                    memory.save_context(
                        {"input": user_input},
                        {"output": bot_response}
                    )
                else:
                    # Fallback for different memory types
                    memory.chat_memory.add_user_message(user_input)
                    memory.chat_memory.add_ai_message(bot_response)
            except Exception as e:
                logger.error(f"Error saving to memory: {e}")
    
    def get_conversation_history(self, user_id: str) -> str:
        """
        Get formatted conversation history for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Formatted conversation history string
        """
        memory = self.get_memory_for_user(user_id)
        
        if isinstance(memory, SimpleMemory):
            return memory.get_context_string()
        else:
            # LangChain memory
            try:
                if hasattr(memory, 'buffer'):
                    return str(memory.buffer)
                elif hasattr(memory, 'chat_memory'):
                    messages = memory.chat_memory.messages
                    history_parts = []
                    for msg in messages[-10:]:  # Last 10 messages
                        if hasattr(msg, 'content'):
                            role = "Human" if isinstance(msg, HumanMessage) else "Assistant"
                            history_parts.append(f"{role}: {msg.content}")
                    return "\n".join(history_parts)
                else:
                    return "No conversation history available"
            except Exception as e:
                logger.error(f"Error retrieving conversation history: {e}")
                return "Error retrieving conversation history"
    
    def clear_user_memory(self, user_id: str):
        """
        Clear memory for a specific user
        
        Args:
            user_id: User identifier
        """
        if user_id in self.user_sessions:
            memory = self.user_sessions[user_id]
            if isinstance(memory, SimpleMemory):
                memory.clear()
            else:
                # LangChain memory
                try:
                    if hasattr(memory, 'clear'):
                        memory.clear()
                    elif hasattr(memory, 'chat_memory'):
                        memory.chat_memory.clear()
                except Exception as e:
                    logger.error(f"Error clearing memory: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about memory usage
        
        Returns:
            Dictionary with memory statistics
        """
        stats = {
            "active_sessions": len(self.user_sessions),
            "memory_type": self.memory_type,
            "sessions": {}
        }
        
        for user_id, memory in self.user_sessions.items():
            if isinstance(memory, SimpleMemory):
                stats["sessions"][user_id] = {
                    "message_count": len(memory.messages),
                    "type": "SimpleMemory"
                }
            else:
                # LangChain memory
                try:
                    message_count = 0
                    if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
                        message_count = len(memory.chat_memory.messages)
                    
                    stats["sessions"][user_id] = {
                        "message_count": message_count,
                        "type": type(memory).__name__
                    }
                except Exception as e:
                    stats["sessions"][user_id] = {
                        "error": str(e),
                        "type": type(memory).__name__
                    }
        
        return stats

# Global memory manager instance
hr_memory_manager = HRBotMemoryManager()

def get_memory_for_session(session_id: str) -> Any:
    """
    Convenience function to get memory for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Memory instance for the session
    """
    return hr_memory_manager.get_memory_for_user(session_id)

if __name__ == "__main__":
    # Test memory functionality
    print("Testing HR Bot Memory...")
    
    # Test simple memory
    simple_mem = SimpleMemory()
    simple_mem.add_message("user", "What are my vacation days?")
    simple_mem.add_message("assistant", "You have 15 vacation days remaining.")
    
    print("Simple Memory Test:")
    print(simple_mem.get_context_string())
    
    # Test memory manager
    manager = HRBotMemoryManager()
    manager.add_interaction("user123", "How do I request time off?", "You can submit leave requests through the HR portal.")
    
    print("\nMemory Manager Test:")
    print(manager.get_conversation_history("user123"))
    
    print("\nMemory Stats:")
    print(manager.get_memory_stats())