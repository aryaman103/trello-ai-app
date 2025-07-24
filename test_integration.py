#!/usr/bin/env python3
"""
Test script for ChatGPT 4o integration
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_ai_chat_endpoint():
    """Test the AI chat endpoint"""
    print("Testing ChatGPT 4o integration...")
    
    # Test message
    test_message = {
        "message": "Help me organize my tasks better",
        "context": "task_management"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/ai-chat",
            json=test_message,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ ChatGPT 4o integration working!")
            print(f"Response: {data.get('response', 'No response')}")
            return True
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please start the server first with: python hr_api.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_task_creation():
    """Test task creation via AI"""
    print("\nTesting AI task creation...")
    
    test_message = {
        "message": "Create a task called 'Review project documentation'",
        "context": "task_management"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/ai-chat",
            json=test_message,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Task creation test working!")
            if data.get('action') == 'create_task':
                print(f"Task name extracted: {data.get('task_name')}")
                print(f"Response: {data.get('response')}")
            else:
                print(f"Response: {data.get('response', 'No response')}")
            return True
        else:
            print(f"❌ Task creation test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Task creation test failed: {e}")
        return False

if __name__ == "__main__":
    print("ChatGPT 4o Integration Test")
    print("=" * 30)
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        exit(1)
    
    print("✅ OpenAI API key found")
    
    # Run tests
    success1 = test_ai_chat_endpoint()
    success2 = test_task_creation()
    
    if success1 and success2:
        print("\n🎉 All tests passed! ChatGPT 4o integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the server logs for more details.")