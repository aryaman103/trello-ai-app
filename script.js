class TrelloAI {
    constructor() {
        this.boards = JSON.parse(localStorage.getItem('trello-boards') || '[]');
        this.aiMessages = [];
        this.hrMessages = [];
        this.hrApiUrl = 'http://localhost:8000'; // HR API endpoint
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

    sendAIMessage() {
        const input = document.getElementById('ai-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.aiMessages.push({ type: 'user', content: message });
        this.renderAIMessages();
        
        input.value = '';
        
        // Simulate AI response
        setTimeout(() => {
            const response = this.generateAIResponse(message);
            this.aiMessages.push({ type: 'ai', content: response });
            this.renderAIMessages();
        }, 1000);
    }

    generateAIResponse(userMessage) {
        const lowerMessage = userMessage.toLowerCase();
        
        // Simple AI response logic
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

    renderAIMessages() {
        const container = document.getElementById('ai-messages');
        container.innerHTML = '';
        
        this.aiMessages.forEach(message => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `ai-message ${message.type}`;
            messageDiv.textContent = message.content;
            container.appendChild(messageDiv);
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
        const url = `${this.hrApiUrl}${endpoint}`;
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
}

// Initialize the application
const app = new TrelloAI();