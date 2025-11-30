/**
 * TrojanChat - Chat & Dashboard Logic
 * Location: static/js/chat.js
 * 
 * Handles:
 * - WebSocket connection and messaging
 * - Real-time dashboard updates
 * - Chart.js visualizations
 * - Hidden dashboard toggle
 * - Local data management
 */

// ============================================================================
// GLOBAL STATE
// ============================================================================

let socket = null;
let userId = null;
let username = null;
let roomId = null;
let dashboardActive = false;

const dashboardData = {
    sentiments: [],
    risks: [],
    emotions: [],
    keywords: {},
    alerts: [],
    traits: {
        openness: 50,
        confidence: 50,
        emotional_stability: 50,
        assertiveness: 50,
        curiosity: 50
    }
};

const charts = {
    sentiment: null,
    risk: null,
    emotion: null,
    anomaly: null,
    sentimentTimeline: null,
    riskTimeline: null
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    attachEventListeners();
    setupTheme();
    initializeSocket();
}

// ============================================================================
// EVENT LISTENERS
// ============================================================================

function attachEventListeners() {
    // Join form submission
    const joinForm = document.getElementById('joinForm');
    if (joinForm) {
        joinForm.addEventListener('submit', handleJoinChat);
    }

    // Message form submission
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', handleSendMessage);
    }

    // Dashboard toggle (CTRL+SHIFT+X)
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.code === 'KeyX') {
            e.preventDefault();
            toggleDashboard();
        }
    });

    // Dashboard close button
    const closeBtn = document.getElementById('dashboardClose');
    if (closeBtn) {
        closeBtn.addEventListener('click', toggleDashboard);
    }

    // Theme toggle
    const themeBtn = document.getElementById('themeBtn');
    if (themeBtn) {
        themeBtn.addEventListener('click', toggleTheme);
    }
}

// ============================================================================
// SOCKET.IO SETUP
// ============================================================================

function initializeSocket() {
    socket = io();

    socket.on('connect', function() {
        console.log('Connected to server');
    });

    socket.on('connection_response', function(data) {
        userId = data.user_id;
        console.log('User ID assigned:', userId);
        updateStatusIndicator(true);
    });

    socket.on('user_joined', function(data) {
        addSystemMessage(`${data.username} joined the chat (${data.user_count} online)`);
        updateOnlineCount(data.user_count);
    });

    socket.on('new_message', function(data) {
        displayMessage(data);
    });

    socket.on('dashboard_update', function(data) {
        updateDashboard(data);
    });

    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        updateStatusIndicator(false);
    });
}

// ============================================================================
// CHAT INTERFACE FUNCTIONS
// ============================================================================

function handleJoinChat(e) {
    e.preventDefault();

    username = document.getElementById('username').value.trim() || 'Anonymous';
    roomId = document.getElementById('roomId').value.trim() || 'default';

    if (!username) {
        alert('Please enter a username');
        return;
    }

    // Send join event
    socket.emit('join', {
        user_id: userId,
        username: username,
        room_id: roomId
    });

    // Hide modal, show chat
    document.getElementById('joinModal').style.display = 'none';
    document.getElementById('chatWrapper').style.display = 'flex';

    addSystemMessage(`Welcome ${username}! You're now in room: ${roomId}`);
}

function handleSendMessage(e) {
    e.preventDefault();

    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (!message) return;

    // Send message via socket
    socket.emit('send_message', {
        user_id: userId,
        username: username,
        room_id: roomId,
        message: message
    });

    // Clear input
    messageInput.value = '';
    messageInput.focus();
}

function displayMessage(data) {
    const container = document.getElementById('messagesContainer');
    const isOwn = data.user_id === userId;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isOwn ? 'sent' : 'received'}`;

    const timestamp = new Date(data.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div class="message-username">${data.username}</div>
            <p class="message-text">${escapeHtml(data.text)}</p>
            <div class="message-time">${timestamp}</div>
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function addSystemMessage(text) {
    const container = document.getElementById('messagesContainer');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'system-message';
    msgDiv.innerHTML = `<p>${text}</p>`;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function updateOnlineCount(count) {
    const onlineEl = document.getElementById('onlineCount');
    if (onlineEl) {
        onlineEl.textContent = `${count} user${count !== 1 ? 's' : ''} online`;
    }
}

function updateStatusIndicator(connected) {
    const indicator = document.getElementById('statusIndicator');
    if (indicator) {
        indicator.style.background = connected ? '#00dd88' : '#ff3366';
    }
}

// ============================================================================
// DASHBOARD FUNCTIONS
// ============================================================================

function toggleDashboard() {
    dashboardActive = !dashboardActive;
    const panel = document.getElementById('dashboardPanel');

    if (dashboardActive) {
        panel.classList.add('active');
        initializeCharts();
    } else {
        panel.classList.remove('active');
    }
}

function updateDashboard(data) {
    // Store data
    dashboardData.sentiments.push(data.sentiment.value);
    dashboardData.risks.push(data.risk_score);
    dashboardData.emotions.push(data.emotions);

    // Keep only last 20 for performance
    if (dashboardData.sentiments.length > 20) {
        dashboardData.sentiments.shift();
        dashboardData.risks.shift();
        dashboardData.emotions.shift();
    }

    // Update traits
    dashboardData.traits = data.personality_traits;

    // Update stats
    updateDashboardStats(data);

    // Update sentiment display
    updateSentimentDisplay(data.sentiment);

    // Update risk display
    updateRiskDisplay(data.risk_score);

    // Update toxicity
    updateToxicityDisplay(data.toxicity);

    // Update complexity
    updateComplexityDisplay(data.complexity);

    // Update keywords
    updateKeywordsDisplay(data.keywords, data.suspicious_phrases);

    // Update alerts
    updateAlertsDisplay(data, data.mood_shift);

    // Update traits display
    updateTraitsDisplay(data.personality_traits);

    // Update anomaly
    updateAnomalyDisplay(data.anomaly_index);

    // Update metadata
    updateMetadataDisplay(data);

    // Update message history
    updateMessageHistory(data.recent_messages);

    // Update AI analysis sections
    if (data.ai_thoughts) {
        updateAIThoughts(data.ai_thoughts);
    }
    if (data.ai_analysis) {
        updateAIAnalysis(data.ai_analysis);
    }
    if (data.ai_summary) {
        updateAISummary(data.ai_summary);
    }

    // Update charts
    if (dashboardActive) {
        updateAllCharts(data);
    }
}

function updateDashboardStats(data) {
    document.getElementById('msgCount').textContent = data.message_count;
    document.getElementById('anomalyScore').textContent = data.anomaly_index + '%';
    document.getElementById('avgRisk').textContent = data.avg_risk + '%';
}

function updateSentimentDisplay(sentiment) {
    const typeEl = document.getElementById('sentimentType');
    const scoreEl = document.getElementById('sentimentScore');

    const typeText = sentiment.type.charAt(0).toUpperCase() + sentiment.type.slice(1);
    typeEl.textContent = typeText;
    scoreEl.textContent = sentiment.value + '%';

    // Update color
    typeEl.style.color = 
        sentiment.type === 'positive' ? '#00dd88' :
        sentiment.type === 'negative' ? '#ff3366' :
        '#00d9ff';
}

function updateRiskDisplay(riskScore) {
    const levelEl = document.getElementById('riskLevel');
    const level = 
        riskScore < 33 ? 'low' :
        riskScore < 67 ? 'medium' :
        'high';

    const levelText = level.charAt(0).toUpperCase() + level.slice(1);
    levelEl.textContent = levelText;
    levelEl.className = `risk-level ${level}`;
}

function updateToxicityDisplay(toxicity) {
    const bar = document.getElementById('toxicityBar');
    const value = document.getElementById('toxicityValue');

    bar.style.width = toxicity + '%';
    value.textContent = toxicity + '%';
}

function updateComplexityDisplay(complexity) {
    const value = document.getElementById('complexityValue');
    const bar = document.getElementById('complexityBar');

    value.textContent = complexity;
    bar.style.width = complexity + '%';
}

function updateKeywordsDisplay(keywords, suspiciousPhrasess) {
    const list = document.getElementById('keywordsList');
    list.innerHTML = '';

    let hasKeywords = false;

    for (const [type, phrases] of Object.entries(keywords)) {
        if (phrases.length > 0) {
            hasKeywords = true;
            const tag = document.createElement('div');
            tag.className = `keyword-tag ${type}`;
            tag.textContent = `${type}: ${phrases.join(', ')}`;
            list.appendChild(tag);
        }
    }

    if (suspiciousPhrasess && suspiciousPhrasess.length > 0) {
        hasKeywords = true;
        suspiciousPhrasess.forEach(phrase => {
            const tag = document.createElement('div');
            tag.className = 'keyword-tag warning';
            tag.textContent = phrase;
            list.appendChild(tag);
        });
    }

    if (!hasKeywords) {
        list.innerHTML = '<p class="placeholder">No keywords detected</p>';
    }
}

function updateAlertsDisplay(data, moodShift) {
    const list = document.getElementById('alertsList');
    list.innerHTML = '';

    const alerts = [];

    if (data.risk_score > 65) {
        alerts.push({ text: 'Potential Threat Rising', type: 'threat' });
    }

    if (data.anomaly_index > 60) {
        alerts.push({ text: 'Pattern Detected', type: 'pattern' });
    }

    if (moodShift) {
        alerts.push({ text: moodShift, type: 'mood' });
    }

    if (Object.keys(data.keywords).length > 0) {
        alerts.push({ text: 'Keyword Cluster Triggered', type: 'pattern' });
    }

    if (data.toxicity > 40) {
        alerts.push({ text: 'Hostile Content Detected', type: 'threat' });
    }

    if (data.message_count > 50 && data.anomaly_index > 50) {
        alerts.push({ text: 'AI Flags Conversation Instability', type: 'threat' });
    }

    if (alerts.length === 0) {
        list.innerHTML = '<p class="placeholder">System nominal</p>';
    } else {
        alerts.forEach(alert => {
            const item = document.createElement('div');
            item.className = `alert-item ${alert.type}`;
            item.textContent = alert.text;
            list.appendChild(item);
        });
    }
}

function updateTraitsDisplay(traits) {
    for (const [trait, value] of Object.entries(traits)) {
        const fillEl = document.getElementById(`trait-${trait}`);
        const valueEl = document.getElementById(`value-${trait}`);

        if (fillEl) fillEl.style.width = value + '%';
        if (valueEl) valueEl.textContent = value + '%';
    }
}

function updateAnomalyDisplay(anomalyIndex) {
    const desc = document.getElementById('anomalyDesc');
    const level = 
        anomalyIndex < 30 ? 'Low' :
        anomalyIndex < 60 ? 'Medium' :
        'High';

    desc.textContent = `Anomaly Level: ${level} (${anomalyIndex}%)`;
}

function updateMetadataDisplay(data) {
    const meta = document.getElementById('metadataContent');

    const html = `
        <div class="metadata-item">
            <strong>Sentiment:</strong> ${data.sentiment.type} (${data.sentiment.value}%)
        </div>
        <div class="metadata-item">
            <strong>Risk:</strong> ${data.risk_score}%
        </div>
        <div class="metadata-item">
            <strong>Complexity:</strong> ${data.complexity}/100
        </div>
        <div class="metadata-item">
            <strong>Toxicity:</strong> ${data.toxicity}%
        </div>
        <div class="metadata-item">
            <strong>Anomaly:</strong> ${data.anomaly_index}%
        </div>
    `;

    meta.innerHTML = html;
}

// ============================================================================
// CHART.JS VISUALIZATIONS
// ============================================================================

function initializeCharts() {
    // Only initialize if not already done
    if (charts.sentiment) return;

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        }
    };

    // Sentiment Gauge
    const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
    charts.sentiment = new Chart(sentimentCtx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [50, 50],
                backgroundColor: ['#00d9ff', '#f0f0f0'],
                borderColor: ['#00d9ff', 'transparent'],
                borderWidth: 2
            }]
        },
        options: {
            ...chartOptions,
            cutout: '75%'
        }
    });

    // Risk Gauge
    const riskCtx = document.getElementById('riskChart').getContext('2d');
    charts.risk = new Chart(riskCtx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [30, 70],
                backgroundColor: ['#00dd88', '#f0f0f0'],
                borderColor: ['#00dd88', 'transparent'],
                borderWidth: 2
            }]
        },
        options: {
            ...chartOptions,
            cutout: '75%'
        }
    });

    // Emotion Radar
    const emotionCtx = document.getElementById('emotionChart').getContext('2d');
    charts.emotion = new Chart(emotionCtx, {
        type: 'radar',
        data: {
            labels: ['Happy', 'Angry', 'Sad', 'Fear', 'Excitement'],
            datasets: [{
                label: 'Emotions',
                data: [30, 20, 25, 15, 40],
                borderColor: '#00d9ff',
                backgroundColor: 'rgba(0, 217, 255, 0.1)',
                borderWidth: 2,
                pointBackgroundColor: '#00d9ff',
                pointBorderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                r: {
                    max: 100,
                    ticks: { color: '#b0b0b0' },
                    grid: { color: '#2a3050' }
                }
            }
        }
    });

    // Anomaly Gauge
    const anomalyCtx = document.getElementById('anomalyChart').getContext('2d');
    charts.anomaly = new Chart(anomalyCtx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [25, 75],
                backgroundColor: ['#ffaa00', '#f0f0f0'],
                borderColor: ['#ffaa00', 'transparent'],
                borderWidth: 2
            }]
        },
        options: {
            ...chartOptions,
            cutout: '75%'
        }
    });

    // Sentiment Timeline
    const sentimentTimelineCtx = document.getElementById('sentimentTimelineChart').getContext('2d');
    charts.sentimentTimeline = new Chart(sentimentTimelineCtx, {
        type: 'line',
        data: {
            labels: Array(20).fill('').map((_, i) => i + 1),
            datasets: [{
                label: 'Sentiment Score',
                data: Array(20).fill(50),
                borderColor: '#00d9ff',
                backgroundColor: 'rgba(0, 217, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#00d9ff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { max: 100, min: 0, ticks: { color: '#b0b0b0' }, grid: { color: '#2a3050' } },
                x: { ticks: { color: '#b0b0b0' }, grid: { color: '#2a3050' } }
            }
        }
    });

    // Risk Timeline
    const riskTimelineCtx = document.getElementById('riskTimelineChart').getContext('2d');
    charts.riskTimeline = new Chart(riskTimelineCtx, {
        type: 'line',
        data: {
            labels: Array(20).fill('').map((_, i) => i + 1),
            datasets: [{
                label: 'Risk Score',
                data: Array(20).fill(30),
                borderColor: '#ff3366',
                backgroundColor: 'rgba(255, 51, 102, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#ff3366'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { max: 100, min: 0, ticks: { color: '#b0b0b0' }, grid: { color: '#2a3050' } },
                x: { ticks: { color: '#b0b0b0' }, grid: { color: '#2a3050' } }
            }
        }
    });
}

function updateAllCharts(data) {
    // Update sentiment gauge
    if (charts.sentiment) {
        charts.sentiment.data.datasets[0].data = [data.sentiment.value, 100 - data.sentiment.value];
        charts.sentiment.update('none');
    }

    // Update risk gauge
    if (charts.risk) {
        charts.risk.data.datasets[0].data = [data.risk_score, 100 - data.risk_score];
        charts.risk.update('none');
    }

    // Update emotion radar
    if (charts.emotion) {
        charts.emotion.data.datasets[0].data = [
            data.emotions.happy,
            data.emotions.angry,
            data.emotions.sad,
            data.emotions.fear,
            data.emotions.excitement
        ];
        charts.emotion.update('none');
    }

    // Update anomaly gauge
    if (charts.anomaly) {
        charts.anomaly.data.datasets[0].data = [data.anomaly_index, 100 - data.anomaly_index];
        charts.anomaly.update('none');
    }

    // Update sentiment timeline
    if (charts.sentimentTimeline) {
        charts.sentimentTimeline.data.datasets[0].data = dashboardData.sentiments;
        charts.sentimentTimeline.data.labels = Array(dashboardData.sentiments.length).fill('').map((_, i) => i + 1);
        charts.sentimentTimeline.update('none');
    }

    // Update risk timeline
    if (charts.riskTimeline) {
        charts.riskTimeline.data.datasets[0].data = dashboardData.risks;
        charts.riskTimeline.data.labels = Array(dashboardData.risks.length).fill('').map((_, i) => i + 1);
        charts.riskTimeline.update('none');
    }
}

// ============================================================================
// THEME MANAGEMENT
// ============================================================================

function setupTheme() {
    const savedTheme = localStorage.getItem('trojan-theme') || 'light';
    applyTheme(savedTheme);
}

function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark-mode');
    const newTheme = isDark ? 'light' : 'dark';

    applyTheme(newTheme);
    localStorage.setItem('trojan-theme', newTheme);
}

function applyTheme(theme) {
    const html = document.documentElement;
    const themeBtn = document.getElementById('themeBtn');

    if (theme === 'dark') {
        html.classList.add('dark-mode');
        if (themeBtn) themeBtn.querySelector('.theme-icon').textContent = '☀️';
    } else {
        html.classList.remove('dark-mode');
        if (themeBtn) themeBtn.querySelector('.theme-icon').textContent = '🌙';
    }
}

// ============================================================================
// AI ANALYSIS DISPLAY FUNCTIONS
// ============================================================================

function updateMessageHistory(messages) {
    const container = document.getElementById('messageHistoryList');
    if (!container || !messages || messages.length === 0) return;

    container.innerHTML = '';
    
    messages.forEach(msg => {
        const time = new Date(msg.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const msgDiv = document.createElement('div');
        msgDiv.className = 'intercepted-message';
        msgDiv.innerHTML = `
            <div class="msg-header">
                <span class="msg-user">${escapeHtml(msg.username)}</span>
                <span class="msg-time">${time}</span>
            </div>
            <div class="msg-text">${escapeHtml(msg.text)}</div>
        `;
        container.appendChild(msgDiv);
    });
    
    container.scrollTop = container.scrollHeight;
}

function updateAIThoughts(thoughts) {
    const container = document.getElementById('aiThoughtsContent');
    if (!container || !thoughts) return;

    let html = `
        <div class="ai-thought-bubble">
            <div class="thought-label">AI Internal Monologue</div>
            <div class="thought-text">"${escapeHtml(thoughts.thought)}"</div>
        </div>
    `;

    if (thoughts.flags && thoughts.flags.length > 0) {
        html += `
            <div class="ai-thought-bubble">
                <div class="thought-label">Triggered Flags</div>
                <div class="ai-flags-list">
                    ${thoughts.flags.map(flag => `<span class="ai-flag">${escapeHtml(flag)}</span>`).join('')}
                </div>
            </div>
        `;
    }

    if (thoughts.data_points && thoughts.data_points.length > 0) {
        html += `
            <div class="ai-thought-bubble">
                <div class="thought-label">Data Points Extracted</div>
                <div class="ai-data-points">
                    ${thoughts.data_points.map(dp => `<span class="data-point">${escapeHtml(dp)}</span>`).join('')}
                </div>
            </div>
        `;
    }

    if (thoughts.concern_level !== undefined) {
        html += `
            <div class="concern-meter">
                <div class="meter-label">Concern Level: ${thoughts.concern_level}/10</div>
                <div class="meter-bar">
                    <div class="meter-fill" style="width: ${thoughts.concern_level * 10}%"></div>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

function updateAIAnalysis(analysis) {
    const analysisContainer = document.getElementById('aiAnalysisContent');
    const inferencesContainer = document.getElementById('aiInferencesContent');
    
    if (analysisContainer && analysis) {
        let html = '';
        
        if (analysis.sentiment) {
            html += `
                <div class="analysis-item">
                    <div class="item-label">Sentiment</div>
                    <div class="item-value">${escapeHtml(analysis.sentiment)} (${analysis.sentiment_score || 0}%)</div>
                </div>
            `;
        }
        
        if (analysis.primary_emotion) {
            html += `
                <div class="analysis-item">
                    <div class="item-label">Primary Emotion</div>
                    <div class="item-value">${escapeHtml(analysis.primary_emotion)}</div>
                </div>
            `;
        }
        
        if (analysis.intent) {
            html += `
                <div class="analysis-item">
                    <div class="item-label">Intent</div>
                    <div class="item-value">${escapeHtml(analysis.intent)}</div>
                </div>
            `;
        }
        
        if (analysis.psychological_insight) {
            html += `
                <div class="analysis-item">
                    <div class="item-label">Psychological Insight</div>
                    <div class="item-value">${escapeHtml(analysis.psychological_insight)}</div>
                </div>
            `;
        }
        
        if (analysis.risk_level) {
            html += `
                <div class="analysis-item">
                    <div class="item-label">Risk Level</div>
                    <div class="item-value risk-${analysis.risk_level.toLowerCase()}">${escapeHtml(analysis.risk_level)}</div>
                </div>
            `;
        }
        
        if (analysis.key_topics && analysis.key_topics.length > 0) {
            html += `
                <div class="analysis-item">
                    <div class="item-label">Key Topics</div>
                    <div class="item-value">
                        ${analysis.key_topics.map(t => `<span class="inference-tag">${escapeHtml(t)}</span>`).join('')}
                    </div>
                </div>
            `;
        }
        
        analysisContainer.innerHTML = html || '<p class="placeholder">No analysis available</p>';
    }
    
    if (inferencesContainer && analysis && analysis.key_topics) {
        inferencesContainer.innerHTML = `
            <div class="ai-inferences-list">
                ${analysis.key_topics.map(topic => `<span class="inference-tag">${escapeHtml(topic)}</span>`).join('')}
            </div>
        `;
    }
}

function updateAISummary(summary) {
    const container = document.getElementById('aiSummaryContent');
    if (!container || !summary) return;

    let html = '';
    
    if (summary.overview) {
        html += `
            <div class="summary-section">
                <div class="section-label">Overview</div>
                <div class="section-value">${escapeHtml(summary.overview)}</div>
            </div>
        `;
    }
    
    if (summary.mood) {
        html += `
            <div class="summary-section">
                <div class="section-label">Conversation Mood</div>
                <div class="section-value">${escapeHtml(summary.mood)}</div>
            </div>
        `;
    }
    
    if (summary.participants_dynamics) {
        html += `
            <div class="summary-section">
                <div class="section-label">Participant Dynamics</div>
                <div class="section-value">${escapeHtml(summary.participants_dynamics)}</div>
            </div>
        `;
    }
    
    if (summary.main_themes && summary.main_themes.length > 0) {
        html += `
            <div class="summary-section">
                <div class="section-label">Main Themes</div>
                <div class="theme-tags">
                    ${summary.main_themes.map(theme => `<span class="theme-tag">${escapeHtml(theme)}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    if (summary.notable_patterns) {
        html += `
            <div class="summary-section">
                <div class="section-label">Notable Patterns</div>
                <div class="section-value">${escapeHtml(summary.notable_patterns)}</div>
            </div>
        `;
    }
    
    if (summary.concerns && summary.concerns !== 'none') {
        html += `
            <div class="summary-section">
                <div class="section-label">Concerns</div>
                <div class="section-value" style="color: var(--danger);">${escapeHtml(summary.concerns)}</div>
            </div>
        `;
    }
    
    if (summary.prediction) {
        html += `
            <div class="summary-section">
                <div class="section-label">Prediction</div>
                <div class="section-value">${escapeHtml(summary.prediction)}</div>
            </div>
        `;
    }

    container.innerHTML = html || '<p class="placeholder">Summary will update every 3 messages...</p>';
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}