"""
HR Bot Tools - LangChain-compatible functions for HR operations
Implements core HR tools as callable functions for the agentic bot
"""

from langchain.tools import tool
from typing import Dict, Any, List
import json
from datetime import datetime, timedelta
import uuid

# Mock database for HR data
HR_DATA = {
    "employees": {
        "emp_001": {
            "name": "John Doe",
            "department": "Engineering",
            "leave_balance": {
                "vacation": 15,
                "sick": 10,
                "personal": 5
            },
            "manager": "Jane Smith"
        },
        "emp_002": {
            "name": "Jane Smith", 
            "department": "Management",
            "leave_balance": {
                "vacation": 20,
                "sick": 12,
                "personal": 8
            },
            "manager": "CEO"
        }
    },
    "policies": {
        "vacation_policy": "Employees are entitled to vacation days based on tenure. New employees receive 15 days, increasing by 1 day per year up to 25 days maximum.",
        "sick_leave_policy": "All employees receive 10 sick days per year. Unused sick days roll over up to 40 days maximum.",
        "remote_work_policy": "Employees may work remotely up to 3 days per week with manager approval.",
        "holiday_schedule": "Company holidays include New Year's Day, Memorial Day, Independence Day, Labor Day, Thanksgiving, and Christmas Day."
    },
    "leave_requests": []
}

@tool
def get_leave_balance(user_id: str) -> Dict[str, Any]:
    """
    Retrieve leave balance for a specific employee
    
    Args:
        user_id: Employee ID to look up
    
    Returns:
        Dictionary containing leave balance information
    """
    employee = HR_DATA["employees"].get(user_id)
    if not employee:
        return {"error": f"Employee {user_id} not found"}
    
    return {
        "employee_name": employee["name"],
        "leave_balance": employee["leave_balance"],
        "status": "success"
    }

@tool
def submit_leave_request(user_id: str, leave_type: str, start_date: str, end_date: str, reason: str) -> Dict[str, Any]:
    """
    Submit a leave request for an employee
    
    Args:
        user_id: Employee ID submitting the request
        leave_type: Type of leave (vacation, sick, personal)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        reason: Reason for leave request
    
    Returns:
        Dictionary containing request submission status
    """
    employee = HR_DATA["employees"].get(user_id)
    if not employee:
        return {"error": f"Employee {user_id} not found"}
    
    # Calculate days requested
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days_requested = (end - start).days + 1
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    # Check available balance
    available_balance = employee["leave_balance"].get(leave_type, 0)
    if days_requested > available_balance:
        return {
            "error": f"Insufficient {leave_type} balance. Requested: {days_requested} days, Available: {available_balance} days"
        }
    
    # Create leave request
    request_id = str(uuid.uuid4())[:8]
    leave_request = {
        "request_id": request_id,
        "user_id": user_id,
        "employee_name": employee["name"],
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "days_requested": days_requested,
        "reason": reason,
        "status": "pending",
        "submitted_at": datetime.now().isoformat()
    }
    
    HR_DATA["leave_requests"].append(leave_request)
    
    return {
        "message": f"Leave request submitted successfully",
        "request_id": request_id,
        "days_requested": days_requested,
        "status": "pending_approval"
    }

@tool
def lookup_policy(topic: str) -> Dict[str, Any]:
    """
    Look up HR policies by topic
    
    Args:
        topic: Policy topic to search for
    
    Returns:
        Dictionary containing policy information
    """
    topic_lower = topic.lower()
    
    # Search for matching policies
    matching_policies = {}
    for policy_key, policy_text in HR_DATA["policies"].items():
        if topic_lower in policy_key.lower() or topic_lower in policy_text.lower():
            matching_policies[policy_key] = policy_text
    
    if not matching_policies:
        # Provide general guidance if no specific policy found
        return {
            "message": f"No specific policy found for '{topic}'. Please contact HR directly for clarification.",
            "available_policies": list(HR_DATA["policies"].keys())
        }
    
    return {
        "topic": topic,
        "policies": matching_policies,
        "status": "found"
    }

@tool
def escalate_to_hr(user_id: str, issue_type: str, description: str) -> Dict[str, Any]:
    """
    Escalate an issue to HR department
    
    Args:
        user_id: Employee ID raising the issue
        issue_type: Type of issue (complaint, question, request)
        description: Detailed description of the issue
    
    Returns:
        Dictionary containing escalation status
    """
    employee = HR_DATA["employees"].get(user_id)
    employee_name = employee["name"] if employee else "Unknown Employee"
    
    ticket_id = str(uuid.uuid4())[:8]
    
    escalation = {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "employee_name": employee_name,
        "issue_type": issue_type,
        "description": description,
        "status": "open",
        "priority": "normal",
        "created_at": datetime.now().isoformat(),
        "assigned_to": "HR Team"
    }
    
    # In a real system, this would be saved to a ticketing system
    print(f"HR Escalation Created: {json.dumps(escalation, indent=2)}")
    
    return {
        "message": "Issue escalated to HR successfully",
        "ticket_id": ticket_id,
        "status": "escalated",
        "next_steps": "HR will review your request and respond within 2 business days"
    }

@tool
def calendar_api(query: str) -> Dict[str, Any]:
    """
    Query calendar information for holidays, events, and scheduling
    
    Args:
        query: Calendar query (holidays, events, schedule)
    
    Returns:
        Dictionary containing calendar information
    """
    query_lower = query.lower()
    
    # Mock calendar data
    current_date = datetime.now()
    
    if "holiday" in query_lower:
        holidays_2024 = [
            {"date": "2024-01-01", "name": "New Year's Day"},
            {"date": "2024-05-27", "name": "Memorial Day"},
            {"date": "2024-07-04", "name": "Independence Day"},
            {"date": "2024-09-02", "name": "Labor Day"},
            {"date": "2024-11-28", "name": "Thanksgiving Day"},
            {"date": "2024-12-25", "name": "Christmas Day"}
        ]
        
        # Filter upcoming holidays
        upcoming_holidays = []
        for holiday in holidays_2024:
            holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
            if holiday_date >= current_date:
                upcoming_holidays.append(holiday)
        
        return {
            "query": query,
            "upcoming_holidays": upcoming_holidays[:3],  # Next 3 holidays
            "total_company_holidays": len(holidays_2024)
        }
    
    elif "schedule" in query_lower or "meeting" in query_lower:
        return {
            "message": "Calendar scheduling feature would integrate with your company's calendar system",
            "available_actions": [
                "View company holidays",
                "Check team availability", 
                "Schedule HR meetings",
                "View upcoming events"
            ]
        }
    
    else:
        return {
            "message": f"Calendar query '{query}' not recognized",
            "available_queries": ["holidays", "schedule", "meetings", "events"]
        }

@tool
def get_employee_directory(search_term: str = "") -> Dict[str, Any]:
    """
    Search employee directory
    
    Args:
        search_term: Name or department to search for
    
    Returns:
        Dictionary containing employee information
    """
    if not search_term:
        # Return department summary
        departments = {}
        for emp_id, emp_data in HR_DATA["employees"].items():
            dept = emp_data["department"]
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(emp_data["name"])
        
        return {
            "departments": departments,
            "total_employees": len(HR_DATA["employees"])
        }
    
    # Search for employees
    search_lower = search_term.lower()
    matching_employees = []
    
    for emp_id, emp_data in HR_DATA["employees"].items():
        if (search_lower in emp_data["name"].lower() or 
            search_lower in emp_data["department"].lower()):
            matching_employees.append({
                "name": emp_data["name"],
                "department": emp_data["department"],
                "manager": emp_data["manager"]
            })
    
    return {
        "search_term": search_term,
        "results": matching_employees,
        "found": len(matching_employees)
    }

# Tool registry for easy access
AVAILABLE_TOOLS = [
    get_leave_balance,
    submit_leave_request,
    lookup_policy,
    escalate_to_hr,
    calendar_api,
    get_employee_directory
]

def get_tools_list():
    """Return list of available tools for agent registration"""
    return AVAILABLE_TOOLS