class TrelloAI {
    constructor() {
        this.boards = JSON.parse(localStorage.getItem('trello-boards') || '[]');
        this.aiMessages = [];
        this.hrMessages = [];
        this.apiUrl = 'http://localhost:8000'; // Enhanced AI API endpoint
        this.sessionId = null; // Track session for conversation continuity
        this.feedbackData = JSON.parse(localStorage.getItem('feedback-data') || '[]');
        this.escalationData = JSON.parse(localStorage.getItem('escalation-data') || '[]');
        this.currentFeedbackMessageId = null;
        this.init();
    }

    init() {
        this.renderBoards();
        this.setupEventListeners();
        this.loadSampleData();
    }

    setupEventListeners() {
        // Board management
        document.getElementById('add-board-btn').addEventListener('click', () => this.showModal('board'));
        
        // AI Panel
        document.getElementById('ai-assist-btn').addEventListener('click', () => this.toggleAIPanel());
        document.getElementById('close-ai-btn').addEventListener('click', () => this.toggleAIPanel());
        document.getElementById('ai-send-btn').addEventListener('click', () => this.sendAIMessage());
        document.getElementById('ai-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendAIMessage();
        });

        // HR Panel
        document.getElementById('hr-bot-btn').addEventListener('click', () => this.toggleHRPanel());
        document.getElementById('close-hr-btn').addEventListener('click', () => this.toggleHRPanel());
        document.getElementById('hr-send-btn').addEventListener('click', () => this.sendHRMessage());
        document.getElementById('hr-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendHRMessage();
        });

        // HR Quick Actions
        document.querySelectorAll('.hr-quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleHRQuickAction(e.target.dataset.action));
        });

        // Modal
        document.getElementById('modal-close').addEventListener('click', () => this.hideModal());
        document.getElementById('modal-cancel').addEventListener('click', () => this.hideModal());
        document.getElementById('modal-confirm').addEventListener('click', () => this.handleModalConfirm());
        
        // Click outside modal to close
        document.getElementById('modal').addEventListener('click', (e) => {
            if (e.target.id === 'modal') this.hideModal();
        });

        // Feedback and Escalation Event Listeners
        this.setupFeedbackEventListeners();
    }

    setupFeedbackEventListeners() {
        // Escalation button
        document.getElementById('escalate-btn').addEventListener('click', () => this.showEscalationModal());

        // Feedback modal
        document.getElementById('feedback-modal-close').addEventListener('click', () => this.hideFeedbackModal());
        document.getElementById('feedback-cancel').addEventListener('click', () => this.hideFeedbackModal());
        document.getElementById('feedback-submit').addEventListener('click', () => this.submitFeedback());

        // Rating buttons
        document.querySelectorAll('.rating-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectRating(e.target.dataset.rating));
        });

        // Escalation modal
        document.getElementById('escalation-modal-close').addEventListener('click', () => this.hideEscalationModal());
        document.getElementById('escalation-cancel').addEventListener('click', () => this.hideEscalationModal());
        document.getElementById('escalation-submit').addEventListener('click', () => this.submitEscalation());

        // Click outside modals to close
        document.getElementById('feedback-modal').addEventListener('click', (e) => {
            if (e.target.id === 'feedback-modal') this.hideFeedbackModal();
        });
        document.getElementById('escalation-modal').addEventListener('click', (e) => {
            if (e.target.id === 'escalation-modal') this.hideEscalationModal();
        });
    }

    loadSampleData() {
        if (this.boards.length === 0) {
            this.boards = [
                {
                    id: 'board-1',
                    title: 'Project Management',
                    lists: [
                        {
                            id: 'list-1',
                            title: 'To Do',
                            cards: [
                                { id: 'card-1', title: 'Plan project architecture', description: 'Define the overall system design and components' },
                                { id: 'card-2', title: 'Set up development environment', description: 'Install necessary tools and configure workspace' }
                            ]
                        },
                        {
                            id: 'list-2',
                            title: 'In Progress',
                            cards: [
                                { id: 'card-3', title: 'Implement user authentication', description: 'Create login/signup functionality', aiSuggested: true }
                            ]
                        },
                        {
                            id: 'list-3',
                            title: 'Done',
                            cards: [
                                { id: 'card-4', title: 'Initial project setup', description: 'Created basic folder structure and files' }
                            ]
                        }
                    ]
                }
            ];
            this.saveBoards();
            this.renderBoards();
        }
    }

    renderBoards() {
        const container = document.getElementById('boards-container');
        container.innerHTML = '';

        this.boards.forEach(board => {
            const boardElement = this.createBoardElement(board);
            container.appendChild(boardElement);
        });
    }

    createBoardElement(board) {
        const boardDiv = document.createElement('div');
        boardDiv.className = 'board';
        boardDiv.innerHTML = `
            <div class="board-header">
                <h2 class="board-title">${board.title}</h2>
                <button class="board-menu" onclick="app.deleteBoardConfirm('${board.id}')">🗑️</button>
            </div>
            <div class="list-container">
                ${board.lists.map(list => this.createListHTML(board.id, list)).join('')}
                <button class="add-card-btn" onclick="app.addList('${board.id}')">+ Add List</button>
            </div>
        `;
        return boardDiv;
    }

    createListHTML(boardId, list) {
        return `
            <div class="list" data-list-id="${list.id}">
                <div class="list-header">
                    <h3 class="list-title">${list.title}</h3>
                    <button class="board-menu" onclick="app.deleteListConfirm('${boardId}', '${list.id}')">🗑️</button>
                </div>
                ${list.cards.map(card => this.createCardHTML(boardId, list.id, card)).join('')}
                <button class="add-card-btn" onclick="app.addCard('${boardId}', '${list.id}')">+ Add Card</button>
            </div>
        `;
    }

    createCardHTML(boardId, listId, card) {
        const aiClass = card.aiSuggested ? ' ai-suggested' : '';
        return `
            <div class="card${aiClass}" data-card-id="${card.id}" onclick="app.editCard('${boardId}', '${listId}', '${card.id}')">
                <div class="card-title">${card.title}</div>
                ${card.description ? `<div class="card-description">${card.description}</div>` : ''}
            </div>
        `;
    }

    showModal(type, data = {}) {
        const modal = document.getElementById('modal');
        const title = document.getElementById('modal-title');
        const input = document.getElementById('modal-input');
        
        this.modalType = type;
        this.modalData = data;
        
        switch (type) {
            case 'board':
                title.textContent = 'Add New Board';
                input.placeholder = 'Enter board name...';
                input.value = '';
                break;
            case 'list':
                title.textContent = 'Add New List';
                input.placeholder = 'Enter list name...';
                input.value = '';
                break;
            case 'card':
                title.textContent = 'Add New Card';
                input.placeholder = 'Enter card title...';
                input.value = '';
                break;
            case 'edit-card':
                title.textContent = 'Edit Card';
                input.placeholder = 'Enter card title...';
                input.value = data.title || '';
                break;
        }
        
        modal.classList.remove('hidden');
        input.focus();
    }

    hideModal() {
        document.getElementById('modal').classList.add('hidden');
        this.modalType = null;
        this.modalData = null;
    }

    handleModalConfirm() {
        const input = document.getElementById('modal-input');
        const value = input.value.trim();
        
        if (!value) return;
        
        switch (this.modalType) {
            case 'board':
                this.createBoard(value);
                break;
            case 'list':
                this.createList(this.modalData.boardId, value);
                break;
            case 'card':
                this.createCard(this.modalData.boardId, this.modalData.listId, value);
                break;
            case 'edit-card':
                this.updateCard(this.modalData.boardId, this.modalData.listId, this.modalData.cardId, value);
                break;
        }
        
        this.hideModal();
    }

    createBoard(title) {
        const board = {
            id: 'board-' + Date.now(),
            title: title,
            lists: []
        };
        this.boards.push(board);
        this.saveBoards();
        this.renderBoards();
    }

    addList(boardId) {
        this.showModal('list', { boardId });
    }

    createList(boardId, title) {
        const board = this.boards.find(b => b.id === boardId);
        if (board) {
            const list = {
                id: 'list-' + Date.now(),
                title: title,
                cards: []
            };
            board.lists.push(list);
            this.saveBoards();
            this.renderBoards();
        }
    }

    addCard(boardId, listId) {
        this.showModal('card', { boardId, listId });
    }

    createCard(boardId, listId, title, aiSuggested = false) {
        const board = this.boards.find(b => b.id === boardId);
        if (board) {
            const list = board.lists.find(l => l.id === listId);
            if (list) {
                const card = {
                    id: 'card-' + Date.now(),
                    title: title,
                    description: '',
                    aiSuggested: aiSuggested
                };
                list.cards.push(card);
                this.saveBoards();
                this.renderBoards();
            }
        }
    }

    editCard(boardId, listId, cardId) {
        const board = this.boards.find(b => b.id === boardId);
        if (board) {
            const list = board.lists.find(l => l.id === listId);
            if (list) {
                const card = list.cards.find(c => c.id === cardId);
                if (card) {
                    this.showModal('edit-card', { boardId, listId, cardId, title: card.title });
                }
            }
        }
    }

    updateCard(boardId, listId, cardId, title) {
        const board = this.boards.find(b => b.id === boardId);
        if (board) {
            const list = board.lists.find(l => l.id === listId);
            if (list) {
                const card = list.cards.find(c => c.id === cardId);
                if (card) {
                    card.title = title;
                    this.saveBoards();
                    this.renderBoards();
                }
            }
        }
    }

    deleteBoardConfirm(boardId) {
        if (confirm('Are you sure you want to delete this board?')) {
            this.boards = this.boards.filter(b => b.id !== boardId);
            this.saveBoards();
            this.renderBoards();
        }
    }

    deleteListConfirm(boardId, listId) {
        if (confirm('Are you sure you want to delete this list?')) {
            const board = this.boards.find(b => b.id === boardId);
            if (board) {
                board.lists = board.lists.filter(l => l.id !== listId);
                this.saveBoards();
                this.renderBoards();
            }
        }
    }

    toggleAIPanel() {
        const panel = document.getElementById('ai-panel');
        panel.classList.toggle('hidden');
    }

    async sendAIMessage() {
        const input = document.getElementById('ai-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        const userMessageId = Date.now().toString();
        this.aiMessages.push({ 
            type: 'user', 
            content: message, 
            id: userMessageId,
            timestamp: new Date().toISOString()
        });
        this.renderAIMessages();
        
        input.value = '';
        
        // Show typing indicator
        this.aiMessages.push({ type: 'ai', content: 'AI is thinking...', isTyping: true });
        this.renderAIMessages();
        
        // Generate enhanced AI response
        try {
            const response = await this.callEnhancedAI(message);
            
            // Remove typing indicator
            this.aiMessages = this.aiMessages.filter(msg => !msg.isTyping);
            
            const aiMessageId = (Date.now() + 1).toString();
            this.aiMessages.push({ 
                type: 'ai', 
                content: response.response, 
                id: aiMessageId,
                timestamp: new Date().toISOString(),
                confidence: response.confidence_score,
                toolsUsed: response.tools_used,
                escalation: response.escalation
            });
            this.renderAIMessages();
            
            // Handle escalation if needed
            if (response.escalation.should_escalate) {
                setTimeout(() => {
                    const escalationMessageId = (Date.now() + 2).toString();
                    this.aiMessages.push({
                        type: 'ai',
                        content: response.escalation_message || 'This request has been escalated for human assistance.',
                        id: escalationMessageId,
                        timestamp: new Date().toISOString(),
                        isEscalation: true
                    });
                    this.renderAIMessages();
                }, 1000);
            }
            
            // Refresh boards if tools were used
            if (response.tools_used.length > 0) {
                setTimeout(() => this.refreshBoardsFromAPI(), 2000);
            }
            
        } catch (error) {
            // Remove typing indicator
            this.aiMessages = this.aiMessages.filter(msg => !msg.isTyping);
            
            const errorMessageId = (Date.now() + 1).toString();
            this.aiMessages.push({ 
                type: 'ai', 
                content: 'I apologize, but I encountered an error connecting to my enhanced AI system. Please check if the backend server is running.',
                id: errorMessageId,
                timestamp: new Date().toISOString(),
                isError: true
            });
            this.renderAIMessages();
            console.error('Enhanced AI API Error:', error);
        }
    }

    async generateAIResponse(userMessage) {
        try {
            // Try to get response from ChatGPT 4o via backend API
            const response = await fetch('/ai-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: userMessage,
                    context: 'task_management'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Check if AI suggested creating a task
                if (data.action === 'create_task' && data.task_name) {
                    this.createAITask(data.task_name);
                    return data.response + ` I've created the task "${data.task_name}" for you.`;
                }
                
                return data.response;
            }
        } catch (error) {
            console.log('ChatGPT API unavailable, using fallback responses:', error);
        }
        
        // Fallback to simple AI logic if API is unavailable
        return this.generateFallbackResponse(userMessage);
    }
    
    generateFallbackResponse(userMessage) {
        const lowerMessage = userMessage.toLowerCase();
        
        // Simple AI response logic (fallback)
        if (lowerMessage.includes('task') || lowerMessage.includes('card')) {
            const suggestions = [
                "I suggest breaking this down into smaller tasks for better tracking.",
                "Consider adding a deadline to this task to improve productivity.",
                "This task might benefit from being moved to a different list based on priority.",
                "I recommend creating subtasks for this complex item."
            ];
            return suggestions[Math.floor(Math.random() * suggestions.length)];
        }
        
        if (lowerMessage.includes('organize') || lowerMessage.includes('structure')) {
            const organizationTips = [
                "Try organizing your boards by project or department for better clarity.",
                "Consider using color coding or labels to categorize different types of tasks.",
                "I recommend creating templates for recurring project types.",
                "Think about implementing a workflow: Backlog → To Do → In Progress → Review → Done"
            ];
            return organizationTips[Math.floor(Math.random() * organizationTips.length)];
        }
        
        if (lowerMessage.includes('help') || lowerMessage.includes('how')) {
            return "I can help you organize tasks, suggest improvements, create cards automatically, and provide productivity tips. What specific area would you like assistance with?";
        }
        
        if (lowerMessage.includes('create') || lowerMessage.includes('add')) {
            // Extract task from message and create it
            const taskMatch = userMessage.match(/create.*?["']([^"']+)["']|add.*?["']([^"']+)["']|create\s+(.+)|add\s+(.+)/i);
            if (taskMatch) {
                const taskName = taskMatch[1] || taskMatch[2] || taskMatch[3] || taskMatch[4];
                this.createAITask(taskName);
                return `I've created a new task: "${taskName}" and added it to your first board. You can find it marked as AI-suggested.`;
            }
            return "I'd be happy to help create tasks! Please specify what task you'd like me to add.";
        }
        
        // Default responses
        const defaultResponses = [
            "I'm here to help you manage your tasks more effectively. What would you like to accomplish?",
            "I can assist with organizing your boards, creating tasks, and improving your workflow. What do you need help with?",
            "Let me know what specific area of task management you'd like to improve, and I'll provide tailored suggestions.",
            "I'm ready to help optimize your productivity. What's your current challenge?"
        ];
        
        return defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
    }

    createAITask(taskName) {
        if (this.boards.length > 0) {
            const firstBoard = this.boards[0];
            if (firstBoard.lists.length > 0) {
                const firstList = firstBoard.lists[0];
                this.createCard(firstBoard.id, firstList.id, taskName, true);
            }
        }
    }

    // Enhanced AI API integration
    async callEnhancedAI(message) {
        const response = await fetch(`${this.apiUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: this.sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        
        // Store session ID for conversation continuity
        if (data.session_id) {
            this.sessionId = data.session_id;
        }

        return data;
    }

    async refreshBoardsFromAPI() {
        try {
            const response = await fetch(`${this.apiUrl}/boards`);
            if (response.ok) {
                const data = await response.json();
                // Update local boards with API data if available
                console.log('Boards refreshed from API:', data);
                // You could merge API boards with local boards here
            }
        } catch (error) {
            console.log('Could not refresh from API:', error);
        }
    }

    renderAIMessages() {
        const container = document.getElementById('ai-messages');
        container.innerHTML = '';
        
        this.aiMessages.forEach(message => {
            const messageContainer = document.createElement('div');
            messageContainer.className = 'ai-message-container';
            if (message.id) {
                messageContainer.setAttribute('data-message-id', message.id);
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `ai-message ${message.type}`;
            if (message.isError) {
                messageDiv.classList.add('error');
            }
            if (message.isEscalation) {
                messageDiv.classList.add('escalation');
            }
            messageDiv.textContent = message.content;
            messageContainer.appendChild(messageDiv);
            
            // Add confidence indicator and tools info for enhanced AI messages
            if (message.type === 'ai' && !message.isTyping && message.confidence !== undefined) {
                const metaDiv = document.createElement('div');
                metaDiv.className = 'ai-message-meta';
                
                // Confidence indicator
                const confidenceSpan = document.createElement('span');
                confidenceSpan.className = 'confidence-indicator';
                const confidenceLevel = message.confidence >= 0.8 ? 'high' : message.confidence >= 0.6 ? 'medium' : 'low';
                confidenceSpan.className += ` confidence-${confidenceLevel}`;
                confidenceSpan.textContent = `Confidence: ${Math.round(message.confidence * 100)}%`;
                metaDiv.appendChild(confidenceSpan);
                
                // Tools used indicator
                if (message.toolsUsed && message.toolsUsed.length > 0) {
                    const toolsSpan = document.createElement('span');
                    toolsSpan.className = 'tools-used';
                    toolsSpan.textContent = `Tools: ${message.toolsUsed.join(', ')}`;
                    metaDiv.appendChild(toolsSpan);
                }
                
                // Escalation indicator
                if (message.escalation && message.escalation.should_escalate) {
                    const escalationSpan = document.createElement('span');
                    escalationSpan.className = 'escalation-indicator';
                    escalationSpan.textContent = `⚠️ Escalated: ${message.escalation.escalation_type}`;
                    metaDiv.appendChild(escalationSpan);
                }
                
                messageContainer.appendChild(metaDiv);
            }
            
            // Add feedback buttons only for AI messages (not user messages or typing indicators)
            if (message.type === 'ai' && !message.isTyping && message.id) {
                const feedbackDiv = document.createElement('div');
                feedbackDiv.className = 'message-feedback';
                
                const thumbsUpBtn = document.createElement('button');
                thumbsUpBtn.className = 'feedback-btn';
                thumbsUpBtn.textContent = '👍';
                thumbsUpBtn.title = 'Helpful';
                thumbsUpBtn.onclick = () => this.showFeedbackModal(message.id, 1);
                
                const thumbsDownBtn = document.createElement('button');
                thumbsDownBtn.className = 'feedback-btn';
                thumbsDownBtn.textContent = '👎';
                thumbsDownBtn.title = 'Not helpful';
                thumbsDownBtn.onclick = () => this.showFeedbackModal(message.id, 0);
                
                feedbackDiv.appendChild(thumbsUpBtn);
                feedbackDiv.appendChild(thumbsDownBtn);
                messageContainer.appendChild(feedbackDiv);
            }
            
            container.appendChild(messageContainer);
        });
        
        container.scrollTop = container.scrollHeight;
    }

    saveBoards() {
        localStorage.setItem('trello-boards', JSON.stringify(this.boards));
    }

    // HR Panel Methods
    toggleHRPanel() {
        const panel = document.getElementById('hr-panel');
        panel.classList.toggle('hidden');
    }

    async sendHRMessage() {
        const input = document.getElementById('hr-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.hrMessages.push({ type: 'user', content: message });
        this.renderHRMessages();
        
        input.value = '';
        
        try {
            const response = await this.callHRAPI('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    user_id: 'emp_001'
                })
            });
            
            if (response.response) {
                this.hrMessages.push({ type: 'hr', content: response.response });
            } else {
                throw new Error('Invalid response format');
            }
        } catch (error) {
            console.error('HR API Error:', error);
            // Fallback to local HR responses
            const fallbackResponse = this.generateHRFallbackResponse(message);
            this.hrMessages.push({ type: 'hr', content: fallbackResponse });
        }
        
        this.renderHRMessages();
    }

    async handleHRQuickAction(action) {
        const actions = {
            'leave-balance': 'What is my current leave balance?',
            'holidays': 'What are the upcoming company holidays?',
            'policies': 'Tell me about HR policies',
            'directory': 'Show me the employee directory'
        };
        
        const message = actions[action];
        if (message) {
            // Simulate user clicking on quick action
            document.getElementById('hr-input').value = message;
            await this.sendHRMessage();
        }
    }

    async callHRAPI(endpoint, options = {}) {
        const url = `${this.apiUrl}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }

    generateHRFallbackResponse(userMessage) {
        const lowerMessage = userMessage.toLowerCase();
        
        if (lowerMessage.includes('leave') || lowerMessage.includes('vacation') || lowerMessage.includes('balance')) {
            return "Your current leave balance:\n• Vacation Days: 15 remaining\n• Sick Days: 10 remaining\n• Personal Days: 5 remaining\n\nWould you like to submit a leave request?";
        }
        
        if (lowerMessage.includes('holiday') || lowerMessage.includes('calendar')) {
            return "Upcoming company holidays:\n• Labor Day: September 2, 2024\n• Thanksgiving: November 28, 2024\n• Christmas: December 25, 2024\n\nAll holidays are paid time off for full-time employees.";
        }
        
        if (lowerMessage.includes('policy') || lowerMessage.includes('policies')) {
            return "HR Policies Available:\n• Leave Policy: Vacation, sick, and personal time guidelines\n• Remote Work Policy: Work-from-home arrangements\n• Benefits: Health insurance, 401k, professional development\n• Code of Conduct: Workplace behavior expectations\n\nWhich policy would you like to know more about?";
        }
        
        if (lowerMessage.includes('directory') || lowerMessage.includes('employee') || lowerMessage.includes('contact')) {
            return "Employee Directory:\n• Engineering: John Doe, Sarah Johnson\n• Management: Jane Smith (Manager)\n• HR: Contact hr@company.com for assistance\n\nFor specific contact information, please contact HR directly.";
        }
        
        return "I'm your HR assistant! I can help you with:\n\n• Leave balance and vacation requests\n• Company holidays and calendar\n• HR policies and procedures\n• Employee directory information\n• Benefits and compensation questions\n\nWhat would you like to know about?";
    }

    renderHRMessages() {
        const container = document.getElementById('hr-messages');
        container.innerHTML = '';
        
        this.hrMessages.forEach(message => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `hr-message ${message.type}`;
            messageDiv.innerHTML = message.content.replace(/\n/g, '<br>');
            container.appendChild(messageDiv);
        });
        
        container.scrollTop = container.scrollHeight;
    }

    // Feedback and Escalation Methods
    showFeedbackModal(messageId, initialRating = null) {
        this.currentFeedbackMessageId = messageId;
        const modal = document.getElementById('feedback-modal');
        const feedbackDetails = document.querySelector('.feedback-details');
        const ratingBtns = document.querySelectorAll('.rating-btn');
        
        // Reset modal state
        ratingBtns.forEach(btn => btn.classList.remove('selected'));
        feedbackDetails.classList.add('hidden');
        document.getElementById('feedback-text').value = '';
        
        // If initial rating provided, select it
        if (initialRating !== null) {
            const selectedBtn = document.querySelector(`[data-rating="${initialRating}"]`);
            if (selectedBtn) {
                selectedBtn.classList.add('selected');
                feedbackDetails.classList.remove('hidden');
            }
        }
        
        modal.classList.remove('hidden');
    }

    hideFeedbackModal() {
        document.getElementById('feedback-modal').classList.add('hidden');
        this.currentFeedbackMessageId = null;
    }

    selectRating(rating) {
        const ratingBtns = document.querySelectorAll('.rating-btn');
        const feedbackDetails = document.querySelector('.feedback-details');
        
        ratingBtns.forEach(btn => btn.classList.remove('selected'));
        document.querySelector(`[data-rating="${rating}"]`).classList.add('selected');
        feedbackDetails.classList.remove('hidden');
    }

    async submitFeedback() {
        const selectedRating = document.querySelector('.rating-btn.selected');
        const feedbackText = document.getElementById('feedback-text').value.trim();
        
        if (!selectedRating || !this.currentFeedbackMessageId) return;
        
        const feedbackData = {
            id: Date.now().toString(),
            messageId: this.currentFeedbackMessageId,
            rating: parseInt(selectedRating.dataset.rating),
            feedback: feedbackText,
            timestamp: new Date().toISOString(),
            type: 'ai_assistant'
        };
        
        this.feedbackData.push(feedbackData);
        localStorage.setItem('feedback-data', JSON.stringify(this.feedbackData));
        
        // Send to backend if available
        try {
            await fetch('/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(feedbackData)
            });
        } catch (error) {
            console.log('Feedback stored locally, backend unavailable:', error);
        }
        
        // Update UI to show feedback was submitted
        const messageContainer = document.querySelector(`[data-message-id="${this.currentFeedbackMessageId}"]`);
        if (messageContainer) {
            const feedbackDiv = messageContainer.querySelector('.message-feedback');
            if (feedbackDiv) {
                feedbackDiv.innerHTML = '<span class="feedback-submitted">✓ Feedback submitted</span>';
            }
        }
        
        this.hideFeedbackModal();
        
        // Show thank you message
        this.aiMessages.push({
            type: 'ai',
            content: 'Thank you for your feedback! It helps us improve the AI assistant.',
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            isSystemMessage: true
        });
        this.renderAIMessages();
    }

    showEscalationModal() {
        document.getElementById('escalation-modal').classList.remove('hidden');
        document.getElementById('issue-type').value = 'technical';
        document.getElementById('issue-description').value = '';
    }

    hideEscalationModal() {
        document.getElementById('escalation-modal').classList.add('hidden');
    }

    async submitEscalation() {
        const issueType = document.getElementById('issue-type').value;
        const description = document.getElementById('issue-description').value.trim();
        
        if (!description) {
            alert('Please provide a description of your issue.');
            return;
        }
        
        const escalationData = {
            id: Date.now().toString(),
            ticketId: `AI-${Date.now().toString().slice(-6)}`,
            issueType: issueType,
            description: description,
            timestamp: new Date().toISOString(),
            status: 'open',
            priority: 'normal',
            source: 'ai_assistant',
            conversationHistory: this.aiMessages.slice(-5) // Include last 5 messages for context
        };
        
        this.escalationData.push(escalationData);
        localStorage.setItem('escalation-data', JSON.stringify(this.escalationData));
        
        // Send to backend if available
        try {
            await fetch('/api/escalate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(escalationData)
            });
        } catch (error) {
            console.log('Escalation stored locally, backend unavailable:', error);
        }
        
        this.hideEscalationModal();
        
        // Add confirmation message to chat
        this.aiMessages.push({
            type: 'ai',
            content: `Your issue has been escalated to our support team. Ticket ID: ${escalationData.ticketId}. You can expect a response within 2 business days.`,
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            isSystemMessage: true
        });
        this.renderAIMessages();
        
        // Auto-escalate severe issues (simulate intelligent escalation)
        if (description.toLowerCase().includes('urgent') || description.toLowerCase().includes('critical')) {
            setTimeout(() => {
                this.aiMessages.push({
                    type: 'ai',
                    content: '🚨 Due to the urgent nature of your request, this has been marked as high priority and escalated to senior support.',
                    id: Date.now().toString(),
                    timestamp: new Date().toISOString(),
                    isSystemMessage: true
                });
                this.renderAIMessages();
            }, 1000);
        }
    }

    // Get feedback analytics (for admin/development purposes)
    getFeedbackAnalytics() {
        const totalFeedback = this.feedbackData.length;
        const positiveFeedback = this.feedbackData.filter(f => f.rating === 1).length;
        const negativeFeedback = this.feedbackData.filter(f => f.rating === 0).length;
        const satisfactionRate = totalFeedback > 0 ? (positiveFeedback / totalFeedback * 100).toFixed(1) : 0;
        
        return {
            totalFeedback,
            positiveFeedback,
            negativeFeedback,
            satisfactionRate: `${satisfactionRate}%`,
            escalations: this.escalationData.length,
            recentFeedback: this.feedbackData.slice(-10)
        };
    }
}

// Initialize the application
const app = new TrelloAI();