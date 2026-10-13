const API_BASE_URL = "/api/v1";
const SESSION_ID = generateSessionId();

function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substr(2, 9);
}

function handleKeyPress(event) {
    if (event.key === 'Enter') sendMessage();
}

function sendQuickReply(text) {
    document.getElementById('userInput').value = text;
    sendMessage();
}

function addMessage(content, isUser = false) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = isUser ? 'You' : 'AI';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = content;
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return contentDiv;
}

function showTyping(show) {
    document.getElementById('typingIndicator').style.display = show ? 'flex' : 'none';
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    if (!message) return;
    addMessage(`<p>${escapeHtml(message)}</p>`, true);
    input.value = '';
    showTyping(true);
    try {
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: SESSION_ID, message: message, user_id: null, language: document.getElementById('languageSelect').value })
        });
        if (!response.ok || !response.body) throw new Error('Streaming unavailable');
        showTyping(false);
        const target = addMessage('<p></p>');
        let buffer = '', answer = '';
        const reader = response.body.getReader(), decoder = new TextDecoder();
        while (true) {
            const {value, done} = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, {stream: true});
            const blocks = buffer.split('\n\n'); buffer = blocks.pop();
            for (const block of blocks) {
                const event = (block.match(/^event: (.+)$/m) || [])[1];
                const raw = (block.match(/^data: (.+)$/m) || [])[1];
                if (!raw) continue;
                const data = JSON.parse(raw);
                if (event === 'token') {
                    answer += data.text; target.querySelector('p').textContent = answer;
                } else if (event === 'complete') {
                    if (data.is_grounded && data.sources?.length) {
                        const sources = document.createElement('div'); sources.className = 'sources';
                        sources.innerHTML = '<strong>Sources:</strong><br>' + data.sources.map(s => `- ${escapeHtml(s.document)} (Page ${escapeHtml(String(s.page))})`).join('<br>');
                        target.appendChild(sources);
                    }
                    updateQuickReplies(data.quick_replies);
                } else if (event === 'error') {
                    target.innerHTML = `<p class="error-message">Error: ${escapeHtml(data.detail)}</p>`;
                }
            }
        }
    } catch (error) {
        showTyping(false);
        addMessage(`<p class="error-message">Connection error. Please restart using: python main.py</p>`);
    }
}

function updateQuickReplies(replies) {
    const container = document.getElementById('quickReplies');
    if (!replies || replies.length === 0) return;
    container.innerHTML = '';
    replies.forEach(reply => {
        const btn = document.createElement('button');
        btn.textContent = reply;
        btn.onclick = () => sendQuickReply(reply);
        container.appendChild(btn);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.onload = () => {
    document.getElementById('userInput').focus();
};
