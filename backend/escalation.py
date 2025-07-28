"""
Escalation and Confidence Threshold System for Trello AI
Determines when to escalate user requests based on confidence and other factors
"""

import re
import datetime
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class EscalationContext:
    """Context information for escalation decisions"""
    confidence_score: float
    user_input: str
    agent_response: str
    tools_used: List[str]
    response_time: float
    session_id: str
    fallback_count: int = 0
    repeated_requests: int = 0

class ConfidenceEvaluator:
    """Evaluates confidence in AI responses"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
    
    def evaluate_response_confidence(self, 
                                   user_input: str, 
                                   agent_response: str, 
                                   tools_used: List[str]) -> float:
        """
        Evaluate confidence in the agent's response
        
        Args:
            user_input: User's original request
            agent_response: Agent's response
            tools_used: List of tools the agent used
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence_factors = []
        
        # Factor 1: Tool usage indicates structured response
        if tools_used:
            tool_confidence = min(len(tools_used) * 0.2 + 0.3, 0.9)
            confidence_factors.append(tool_confidence)
        else:
            confidence_factors.append(0.3)  # Lower confidence for text-only responses
        
        # Factor 2: Response length and detail
        response_length = len(agent_response.split())
        if response_length > 50:
            length_confidence = min(response_length / 100, 0.9)
        elif response_length > 20:
            length_confidence = 0.7
        elif response_length > 10:
            length_confidence = 0.5
        else:
            length_confidence = 0.3
        confidence_factors.append(length_confidence)
        
        # Factor 3: Specific action keywords
        action_keywords = [
            'created', 'added', 'updated', 'found', 'completed', 
            'successfully', 'generated', 'here are', 'i can help'
        ]
        action_count = sum(1 for keyword in action_keywords 
                          if keyword in agent_response.lower())
        action_confidence = min(action_count * 0.1 + 0.4, 0.8)
        confidence_factors.append(action_confidence)
        
        # Factor 4: Error indicators reduce confidence
        error_keywords = ['sorry', 'cannot', 'unable', 'error', 'failed', 'not found']
        error_count = sum(1 for keyword in error_keywords 
                         if keyword in agent_response.lower())
        error_penalty = max(0.2, 1.0 - error_count * 0.2)
        confidence_factors.append(error_penalty)
        
        # Factor 5: Question vs statement analysis
        if '?' in user_input:
            # Question - check if response provides clear answer
            if any(word in agent_response.lower() for word in ['yes', 'no', 'here', 'found']):
                question_confidence = 0.8
            else:
                question_confidence = 0.5
        else:
            # Command/request - check if action was taken
            if tools_used:
                question_confidence = 0.9
            else:
                question_confidence = 0.4
        confidence_factors.append(question_confidence)
        
        # Calculate weighted average
        final_confidence = sum(confidence_factors) / len(confidence_factors)
        return round(final_confidence, 2)

class EscalationSystem:
    """Manages escalation decisions and logging"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.confidence_evaluator = ConfidenceEvaluator(confidence_threshold)
        self.escalation_log = []
        
        # Escalation triggers
        self.user_escalation_phrases = [
            "talk to a human", "this isn't working", "i need help", 
            "human assistance", "escalate", "not helpful", "frustrated"
        ]
        
        self.sensitive_keywords = [
            "bug", "error", "broken", "not working", "delete all", 
            "lost data", "critical", "urgent", "deadline"
        ]
    
    def should_escalate(self, context: EscalationContext) -> Dict[str, Any]:
        """
        Determine if a request should be escalated
        
        Args:
            context: EscalationContext with all relevant information
            
        Returns:
            Dictionary with escalation decision and reasoning
        """
        escalation_reasons = []
        escalate = False
        
        # 1. Confidence threshold check
        if context.confidence_score < self.confidence_threshold:
            escalation_reasons.append(f"Low confidence score: {context.confidence_score}")
            escalate = True
        
        # 2. User explicitly requesting escalation
        if self._user_requested_escalation(context.user_input):
            escalation_reasons.append("User explicitly requested human assistance")
            escalate = True
        
        # 3. Repeated failed attempts
        if context.fallback_count >= 2:
            escalation_reasons.append(f"Multiple fallback attempts: {context.fallback_count}")
            escalate = True
        
        # 4. Sensitive topic detection
        if self._contains_sensitive_content(context.user_input):
            escalation_reasons.append("Sensitive topic detected")
            escalate = True
        
        # 5. Repeated identical requests
        if context.repeated_requests >= 3:
            escalation_reasons.append(f"Repeated similar requests: {context.repeated_requests}")
            escalate = True
        
        # 6. Complex request with no tool usage
        if (len(context.user_input.split()) > 20 and 
            not context.tools_used and 
            context.confidence_score < 0.6):
            escalation_reasons.append("Complex request with low tool engagement")
            escalate = True
        
        escalation_decision = {
            "should_escalate": escalate,
            "confidence_score": context.confidence_score,
            "threshold": self.confidence_threshold,
            "reasons": escalation_reasons,
            "escalation_type": self._determine_escalation_type(escalation_reasons),
            "priority": self._determine_priority(context, escalation_reasons)
        }
        
        if escalate:
            self._log_escalation(context, escalation_decision)
        
        return escalation_decision
    
    def _user_requested_escalation(self, user_input: str) -> bool:
        """Check if user explicitly requested escalation"""
        user_lower = user_input.lower()
        return any(phrase in user_lower for phrase in self.user_escalation_phrases)
    
    def _contains_sensitive_content(self, user_input: str) -> bool:
        """Check for sensitive keywords that should trigger escalation"""
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in self.sensitive_keywords)
    
    def _determine_escalation_type(self, reasons: List[str]) -> str:
        """Determine the type of escalation based on reasons"""
        if any("sensitive" in reason.lower() for reason in reasons):
            return "sensitive_content"
        elif any("user explicitly" in reason.lower() for reason in reasons):
            return "user_requested"
        elif any("confidence" in reason.lower() for reason in reasons):
            return "low_confidence"
        elif any("repeated" in reason.lower() for reason in reasons):
            return "repeated_attempts"
        else:
            return "general"
    
    def _determine_priority(self, context: EscalationContext, reasons: List[str]) -> str:
        """Determine escalation priority"""
        # High priority conditions
        if (any("sensitive" in reason.lower() for reason in reasons) or
            any("urgent" in context.user_input.lower() or "critical" in context.user_input.lower())):
            return "high"
        
        # Medium priority conditions
        if (context.confidence_score < 0.4 or 
            context.repeated_requests >= 2):
            return "medium"
        
        return "low"
    
    def _log_escalation(self, context: EscalationContext, decision: Dict[str, Any]):
        """Log escalation for review"""
        escalation_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": context.session_id,
            "user_input": context.user_input,
            "agent_response": context.agent_response,
            "confidence_score": context.confidence_score,
            "decision": decision,
            "context": asdict(context)
        }
        
        self.escalation_log.append(escalation_entry)
        
        # Save to file for review
        try:
            with open("escalation_log.json", "w") as f:
                json.dump(self.escalation_log, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save escalation log: {e}")
    
    def get_escalation_message(self, escalation_type: str, priority: str) -> str:
        """Generate appropriate escalation message"""
        base_message = "I understand you need additional assistance. "
        
        if escalation_type == "sensitive_content":
            return (f"{base_message}This appears to be a sensitive issue that requires "
                   "human attention. A support specialist will review your request.")
        
        elif escalation_type == "user_requested":
            return (f"{base_message}I'll connect you with a human assistant who can "
                   "provide more personalized help with your Trello board management.")
        
        elif escalation_type == "low_confidence":
            return (f"{base_message}I want to make sure you get the best help possible. "
                   "Let me connect you with someone who can better assist with your request.")
        
        elif escalation_type == "repeated_attempts":
            return (f"{base_message}I notice we've been working on this together. "
                   "A human assistant can provide a fresh perspective on your Trello needs.")
        
        else:
            return (f"{base_message}For the best assistance with your Trello board, "
                   "I'll escalate this to a human specialist.")
    
    def get_escalation_stats(self) -> Dict[str, Any]:
        """Get statistics about escalations"""
        if not self.escalation_log:
            return {"total_escalations": 0}
        
        total = len(self.escalation_log)
        
        # Count by type
        type_counts = {}
        priority_counts = {}
        
        for entry in self.escalation_log:
            esc_type = entry["decision"]["escalation_type"]
            priority = entry["decision"]["priority"]
            
            type_counts[esc_type] = type_counts.get(esc_type, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Average confidence score of escalated requests
        avg_confidence = sum(entry["confidence_score"] for entry in self.escalation_log) / total
        
        return {
            "total_escalations": total,
            "escalation_types": type_counts,
            "priority_distribution": priority_counts,
            "average_confidence_when_escalated": round(avg_confidence, 2),
            "confidence_threshold": self.confidence_threshold
        }

# Global escalation system instance
escalation_system = EscalationSystem()

def evaluate_and_escalate(user_input: str, 
                         agent_response: str, 
                         tools_used: List[str],
                         session_id: str,
                         response_time: float = 0.0,
                         fallback_count: int = 0,
                         repeated_requests: int = 0) -> Dict[str, Any]:
    """
    Convenience function to evaluate confidence and determine escalation
    
    Returns:
        Dictionary with confidence score and escalation decision
    """
    # Evaluate confidence
    confidence_score = escalation_system.confidence_evaluator.evaluate_response_confidence(
        user_input, agent_response, tools_used
    )
    
    # Create context
    context = EscalationContext(
        confidence_score=confidence_score,
        user_input=user_input,
        agent_response=agent_response,
        tools_used=tools_used,
        response_time=response_time,
        session_id=session_id,
        fallback_count=fallback_count,
        repeated_requests=repeated_requests
    )
    
    # Check escalation
    escalation_decision = escalation_system.should_escalate(context)
    
    return {
        "confidence_score": confidence_score,
        "escalation": escalation_decision,
        "escalation_message": escalation_system.get_escalation_message(
            escalation_decision["escalation_type"],
            escalation_decision["priority"]
        ) if escalation_decision["should_escalate"] else None
    }