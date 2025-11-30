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

    // ====== NEW ADVANCED FEATURES ======
    
    // Threat level and energy
    if (data.threat_level) {
        updateThreatLevel(data.threat_level);
    }
    if (data.ai_energy !== undefined) {
        updateAIEnergy(data.ai_energy);
    }
    if (data.velocity) {
        updateVelocity(data.velocity);
    }
    
    // Topic and tone
    if (data.topic) {
        updateTopicDisplay(data.topic);
    }
    if (data.tone) {
        updateToneDisplay(data.tone);
    }
    
    // Mental stress and security
    if (data.mental_stress) {
        updateMentalStress(data.mental_stress);
    }
    updateSecurityChecks(data.spam_detection, data.phishing, data.unsafe_links);
    
    // Personality fingerprint and intent
    if (data.personality_fingerprint) {
        updatePersonalityFingerprint(data.personality_fingerprint);
    }
    if (data.ai_intent) {
        updateIntentDisplay(data.ai_intent);
    }
    
    // Word cloud
    if (data.word_cloud) {
        updateWordCloud(data.word_cloud);
    }
    
    // AI emotional mirror and prediction
    if (data.ai_emotional_mirror) {
        updateAIEmotionalMirror(data.ai_emotional_mirror);
    }
    if (data.ai_prediction) {
        updateAIPrediction(data.ai_prediction);
    }
    
    // Reply suggestions
    if (data.ai_replies) {
        updateReplySuggestions(data.ai_replies);
    }
    
    // Notification center
    if (data.alerts) {
        updateNotificationCenter(data.alerts);
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
// NEW ADVANCED FEATURES DISPLAY FUNCTIONS
// ============================================================================

function updateThreatLevel(threatLevel) {
    const badge = document.getElementById('threatBadge');
    if (!badge || !threatLevel) return;
    
    const indicator = badge.querySelector('.threat-indicator');
    const label = badge.querySelector('.threat-label');
    const score = badge.querySelector('.threat-score');
    
    indicator.className = `threat-indicator ${threatLevel.level}`;
    label.textContent = threatLevel.label;
    score.textContent = threatLevel.score + '%';
}

function updateAIEnergy(energy) {
    const bar = document.getElementById('energyBar');
    const value = document.getElementById('energyValue');
    if (!bar || energy === undefined) return;
    
    const fill = bar.querySelector('.energy-fill');
    fill.style.width = energy + '%';
    value.textContent = energy + '%';
    
    fill.style.background = energy > 70 ? 'var(--danger)' : energy > 40 ? 'var(--warning)' : 'var(--success)';
}

function updateVelocity(velocity) {
    const dial = document.getElementById('velocityDial');
    const value = document.getElementById('velocityValue');
    const status = document.getElementById('velocityStatus');
    if (!dial || !velocity) return;
    
    value.textContent = velocity.velocity;
    status.textContent = velocity.status.charAt(0).toUpperCase() + velocity.status.slice(1);
    status.className = `velocity-status ${velocity.status}`;
    
    if (velocity.burst_detected) {
        dial.classList.add('burst');
    } else {
        dial.classList.remove('burst');
    }
}

function updateTopicDisplay(topic) {
    const container = document.getElementById('topicTags');
    if (!container || !topic) return;
    
    container.innerHTML = '';
    for (const [topicName, score] of Object.entries(topic)) {
        const tag = document.createElement('span');
        tag.className = 'topic-tag';
        tag.innerHTML = `${topicName} <small>(${score}%)</small>`;
        container.appendChild(tag);
    }
}

function updateToneDisplay(tone) {
    const container = document.getElementById('toneDisplay');
    if (!container || !tone) return;
    
    const primary = container.querySelector('.tone-primary');
    const bar = container.querySelector('.tone-bar');
    
    primary.textContent = tone.primary.charAt(0).toUpperCase() + tone.primary.slice(1);
    bar.style.width = tone.confidence + '%';
}

function updateMentalStress(stress) {
    const fill = document.getElementById('stressFill');
    const alerts = document.getElementById('stressAlerts');
    if (!fill || !stress) return;
    
    fill.style.width = stress.warning_level + '%';
    fill.style.background = stress.alert ? 'var(--danger)' : 'var(--success)';
    
    if (stress.indicators && Object.keys(stress.indicators).length > 0) {
        alerts.innerHTML = Object.entries(stress.indicators)
            .map(([category, keywords]) => `<div class="stress-alert ${category}">${category}: ${keywords.join(', ')}</div>`)
            .join('');
    } else {
        alerts.innerHTML = '<p class="placeholder">No stress indicators detected</p>';
    }
}

function updateSecurityChecks(spam, phishing, links) {
    const spamCheck = document.getElementById('spamCheck');
    const phishingCheck = document.getElementById('phishingCheck');
    const linkCheck = document.getElementById('linkCheck');
    
    if (spamCheck && spam) {
        const icon = spamCheck.querySelector('.check-icon');
        const status = spamCheck.querySelector('.check-status');
        icon.textContent = spam.is_bot ? '⚠' : '✓';
        status.textContent = spam.is_bot ? 'Detected!' : 'Clear';
        status.className = `check-status ${spam.is_bot ? 'danger' : 'safe'}`;
    }
    
    if (phishingCheck && phishing) {
        const icon = phishingCheck.querySelector('.check-icon');
        const status = phishingCheck.querySelector('.check-status');
        icon.textContent = phishing.is_phishing ? '⚠' : '✓';
        status.textContent = phishing.is_phishing ? 'Alert!' : 'Clear';
        status.className = `check-status ${phishing.is_phishing ? 'danger' : 'safe'}`;
    }
    
    if (linkCheck && links) {
        const icon = linkCheck.querySelector('.check-icon');
        const status = linkCheck.querySelector('.check-status');
        icon.textContent = links.count > 0 ? '⚠' : '✓';
        status.textContent = links.count > 0 ? `${links.count} Suspicious` : 'Clear';
        status.className = `check-status ${links.count > 0 ? 'warning' : 'safe'}`;
    }
}

function updatePersonalityFingerprint(fingerprint) {
    const typeEl = document.getElementById('fingerprintType');
    if (!typeEl || !fingerprint) return;
    
    typeEl.textContent = fingerprint.type.charAt(0).toUpperCase() + fingerprint.type.slice(1);
    typeEl.className = `fingerprint-type ${fingerprint.type}`;
    
    if (fingerprint.patterns) {
        for (const [pattern, value] of Object.entries(fingerprint.patterns)) {
            const bar = document.getElementById(`pattern-${pattern}`);
            if (bar) {
                bar.style.width = Math.min(100, value * 20) + '%';
            }
        }
    }
}

function updateIntentDisplay(intent) {
    const primary = document.getElementById('intentPrimary');
    const subtext = document.getElementById('intentSubtext');
    if (!primary || !intent) return;
    
    primary.textContent = intent.primary_intent ? 
        intent.primary_intent.charAt(0).toUpperCase() + intent.primary_intent.slice(1) : 'Unknown';
    
    if (intent.emotional_subtext) {
        subtext.textContent = intent.emotional_subtext;
    }
}

function updateWordCloud(words) {
    const container = document.getElementById('wordcloudContainer');
    if (!container || !words || words.length === 0) return;
    
    container.innerHTML = '';
    words.forEach(word => {
        const span = document.createElement('span');
        span.className = 'word-cloud-word';
        span.style.fontSize = word.size + 'px';
        span.style.opacity = 0.5 + (word.count / 10);
        span.textContent = word.word;
        container.appendChild(span);
    });
}

function updateAIEmotionalMirror(mirror) {
    const feeling = document.getElementById('aiFeeling');
    const response = document.getElementById('aiResponse');
    const intensity = document.getElementById('intensityFill');
    if (!feeling || !mirror) return;
    
    const emojiMap = {
        'curious': '🤔',
        'concerned': '😟',
        'amused': '😄',
        'alarmed': '😨',
        'intrigued': '🧐',
        'neutral': '🤖'
    };
    
    feeling.querySelector('.feeling-emoji').textContent = emojiMap[mirror.ai_feeling] || '🤖';
    feeling.querySelector('.feeling-text').textContent = mirror.ai_feeling || 'Neutral';
    
    if (mirror.emotional_response) {
        response.innerHTML = `<p>${escapeHtml(mirror.emotional_response)}</p>`;
    }
    
    if (intensity && mirror.intensity !== undefined) {
        intensity.style.width = mirror.intensity + '%';
    }
}

function updateAIPrediction(prediction) {
    const container = document.getElementById('predictionContent');
    if (!container) return;
    
    if (!prediction) {
        container.innerHTML = '<p class="placeholder">AI will predict the next message...</p>';
        return;
    }
    
    container.innerHTML = `
        <div class="prediction-text">"${escapeHtml(prediction.prediction)}"</div>
        <div class="prediction-meta">
            <span class="confidence">Confidence: ${prediction.confidence}%</span>
            <span class="reasoning">${escapeHtml(prediction.reasoning)}</span>
        </div>
    `;
}

function updateReplySuggestions(replies) {
    if (!replies) return;
    
    const casual = document.getElementById('replyCasual');
    const thoughtful = document.getElementById('replyThoughtful');
    const brief = document.getElementById('replyBrief');
    
    if (casual && replies.casual) casual.textContent = replies.casual;
    if (thoughtful && replies.thoughtful) thoughtful.textContent = replies.thoughtful;
    if (brief && replies.brief) brief.textContent = replies.brief;
}

function updateNotificationCenter(alerts) {
    const container = document.getElementById('notificationList');
    if (!container) return;
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<p class="placeholder">Notifications will appear here...</p>';
        return;
    }
    
    container.innerHTML = '';
    alerts.forEach(alert => {
        const notif = document.createElement('div');
        notif.className = `notification-item ${alert.level}`;
        notif.innerHTML = `
            <span class="notif-icon">${alert.level === 'danger' ? '🚨' : alert.level === 'warning' ? '⚠️' : 'ℹ️'}</span>
            <span class="notif-message">${escapeHtml(alert.message)}</span>
            <span class="notif-type">${alert.type}</span>
        `;
        container.appendChild(notif);
    });
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