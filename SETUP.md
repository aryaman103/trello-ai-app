# HR Bot Setup Instructions

This document provides step-by-step instructions for setting up the HR Bot functionality in your Trello AI application.

## Quick Start

1. **Open the application**: Open `index.html` in your web browser
2. **Click the HR Bot button**: The green "👥 HR Bot" button in the header
3. **Start chatting**: Use the HR panel that slides in from the left

The HR Bot works with fallback responses even without the backend API running!

## Backend API Setup (Optional)

For advanced features and LangChain integration, you can set up the backend API:

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** (optional):
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

3. **Start the HR API server**:
   ```bash
   python hr_api.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn hr_api:app --reload --port 8000
   ```

4. **Verify the API**:
   - Open http://localhost:8000 in your browser
   - Check health status at http://localhost:8000/health
   - View API documentation at http://localhost:8000/docs

## Features

### Frontend Features (Always Available)

- **HR Chat Interface**: Chat with the HR bot using natural language
- **Quick Actions**: One-click buttons for common HR queries
- **Fallback Responses**: Works without backend API
- **Responsive Design**: Works on desktop and mobile

### Backend Features (When API is Running)

- **LangChain Integration**: Advanced conversational AI
- **Knowledge Base**: Document-based question answering
- **Memory Management**: Conversation history tracking
- **Tool Integration**: Leave requests, policy lookup, etc.

## HR Bot Capabilities

### Core Functions

1. **Leave Management**
   - Check leave balance
   - Submit leave requests
   - View leave policies

2. **Company Information**
   - Company holidays calendar
   - Employee directory
   - HR policies and procedures

3. **Knowledge Base Queries**
   - Employee handbook information
   - Benefits information
   - Expense policies

### Quick Actions

- **Check Leave Balance**: Instantly view remaining vacation/sick days
- **Company Holidays**: See upcoming holidays and dates
- **HR Policies**: Access policy information
- **Employee Directory**: Search for employee contacts

## Customization

### Adding HR Documents

1. Place HR documents in `data_ingest/documents/`
2. Supported formats: `.txt`, `.md`, `.pdf` (with proper setup)
3. Restart the API server to reload documents

### Modifying HR Tools

Edit `agents/tools.py` to:
- Add new HR functions
- Modify mock data
- Integrate with real HR systems

### Customizing Responses

Edit `agents/basic_agent.py` to:
- Modify conversation logic
- Add new response patterns
- Integrate with external APIs

## Architecture

```
trello-ai-app/
├── agents/                 # HR agent logic
│   ├── tools.py           # HR tools and functions
│   └── basic_agent.py     # Main agent implementation
├── data_ingest/           # Knowledge base
│   ├── ingest.py         # Document processing
│   └── documents/        # HR documents directory
├── memory/                # Conversation memory
│   └── memory.py         # Memory management
├── hr_api.py             # FastAPI backend server
├── index.html            # Main application
├── script.js             # Frontend logic (includes HR bot)
├── styles.css            # Styling (includes HR panel styles)
└── requirements.txt      # Python dependencies
```

## API Endpoints

When the backend is running, these endpoints are available:

- `GET /` - API information
- `GET /health` - Health check
- `POST /chat` - Chat with HR bot
- `POST /leave/balance` - Get leave balance
- `POST /leave/request` - Submit leave request
- `POST /policy/lookup` - Look up policies
- `GET /calendar/holidays` - Get holidays
- `GET /directory` - Search employee directory

## Troubleshooting

### Frontend Issues

- **HR panel not opening**: Check browser console for JavaScript errors
- **Styles not loading**: Ensure `styles.css` is properly linked
- **Quick actions not working**: Verify event listeners are attached

### Backend Issues

- **API not starting**: Check Python version and dependencies
- **Import errors**: Install missing packages with pip
- **OpenAI errors**: Verify API key is set correctly
- **Memory issues**: Check conversation storage and cleanup

### Common Solutions

1. **Clear browser cache** if frontend changes aren't visible
2. **Check console logs** for detailed error messages
3. **Verify file paths** are correct for your setup
4. **Test with fallback mode** first before enabling API

## Development

### Testing the HR Bot

1. Test frontend-only mode by opening `index.html`
2. Test API integration by starting `hr_api.py`
3. Try different HR queries and quick actions
4. Verify conversation memory persistence

### Adding New Features

1. Add new tools in `agents/tools.py`
2. Update agent logic in `agents/basic_agent.py`
3. Add new API endpoints in `hr_api.py`
4. Update frontend in `script.js` for new UI features

## Security Notes

- The current implementation uses mock data for demonstration
- In production, integrate with real HR systems securely
- Implement proper authentication and authorization
- Validate all user inputs and sanitize outputs
- Use HTTPS in production environments

## Support

For issues or questions:
1. Check the console logs for error messages
2. Verify all dependencies are installed correctly
3. Test with the fallback mode first
4. Review the API documentation at `/docs` when backend is running