#!/usr/bin/env python3
"""
Trello AI Enhanced Server Startup Script
Starts the FastAPI backend with LangChain and GPT-4 integration
"""

import os
import sys
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables")
        print("   The agent will run in fallback mode without LangChain integration")
        print("   To enable full AI features:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your OpenAI API key to the .env file")
        print()
    
    # Start the server
    print("🚀 Starting Trello AI Enhanced Server...")
    print("📊 Features enabled:")
    print("   ✅ LangChain Agent Framework")
    print("   ✅ GPT-4 Integration (if API key provided)")
    print("   ✅ Structured Tools for Trello Operations")
    print("   ✅ Confidence Threshold & Smart Escalation")
    print("   ✅ Memory Management & Session Tracking")
    print("   ✅ REST API Endpoints")
    print()
    
    try:
        import uvicorn
        from backend.api import app
        
        # Run the server
        uvicorn.run(
            app,
            host="localhost",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Error: Missing required dependencies")
        print(f"   Please install requirements: pip install -r requirements.txt")
        print(f"   Error details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()