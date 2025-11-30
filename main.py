"""
TrojanChat - Real-Time Ethical Cyber Intelligence Simulator
Science Exhibition Project: "The Trojan Machine - Mechanical Intelligence With Hidden Functions"

This is a production-quality educational project demonstrating how hidden intelligence systems
could theoretically exist within innocent-looking applications. All analysis is simulated locally
without actual spying, data storage, or external transmission. Purpose: Cyber awareness education.
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
from datetime import datetime
import random
import math
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trojan-exhibition-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================================================
# GLOBAL STATE MANAGEMENT
# ============================================================================

chat_rooms = {}
user_sessions = {}
analysis_history = {
    'sentiment': [],
    'emotions': [],
    'keywords': [],
    'messages': [],
    'risks': []
}

class ChatRoom:
    def __init__(self, room_id):
        self.room_id = room_id
        self.users = {}
        self.messages = []
        self.analysis_data = {
            'sentiments': [],
            'emotions_track': [],
            'keywords_freq': {},
            'risk_scores': [],
            'message_count': 0,
            'personality_traits': {
                'openness': 50,
                'confidence': 50,
                'emotional_stability': 50,
                'assertiveness': 50,
                'curiosity': 50
            },
            'anomaly_index': 0,
            'mood_shifts': []
        }

    def add_user(self, user_id, username):
        self.users[user_id] = {'username': username, 'joined_at': datetime.now()}

    def remove_user(self, user_id):
        if user_id in self.users:
            del self.users[user_id]

# ============================================================================
# SIMULATED AI ANALYSIS ENGINE - LOCAL ONLY, NO EXTERNAL CALLS
# ============================================================================

class SimulatedAIAnalyzer:
    """
    All analysis is simulated locally using heuristics, scoring formulas,
    and randomization. No real AI, no data transmission, no storage.
    """

    DANGER_KEYWORDS = ['danger', 'attack', 'threat', 'bomb', 'weapon', 'kill', 'destroy']
    LOVE_KEYWORDS = ['love', 'adore', 'cherish', 'care', 'sweet', 'beautiful', 'amazing']
    THREAT_KEYWORDS = ['threat', 'warn', 'danger', 'careful', 'risk', 'beware']
    HELP_KEYWORDS = ['help', 'assist', 'support', 'aid', 'please', 'urgent']
    DEPRESSION_KEYWORDS = ['sad', 'depressed', 'lonely', 'hopeless', 'lost', 'broken']
    MONEY_KEYWORDS = ['money', 'cash', 'payment', 'price', 'cost', 'bitcoin', 'crypto']
    LOCATION_KEYWORDS = ['location', 'address', 'street', 'city', 'coordinates', 'meet']

    POSITIVE_WORDS = ['good', 'great', 'awesome', 'excellent', 'wonderful', 'happy', 'love', 
                      'amazing', 'fantastic', 'brilliant', 'perfect', 'beautiful']
    NEGATIVE_WORDS = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'disgusting', 'annoying',
                      'sad', 'angry', 'upset', 'disappointed', 'failed']

    @staticmethod
    def analyze_sentiment(text):
        """Simulate sentiment analysis: positive, negative, or neutral."""
        text_lower = text.lower()
        pos_score = sum(1 for word in SimulatedAIAnalyzer.POSITIVE_WORDS if word in text_lower)
        neg_score = sum(1 for word in SimulatedAIAnalyzer.NEGATIVE_WORDS if word in text_lower)

        if pos_score > neg_score and pos_score > 0:
            return 'positive', pos_score * 15 + random.randint(5, 10)
        elif neg_score > pos_score and neg_score > 0:
            return 'negative', neg_score * 12 + random.randint(5, 10)
        else:
            return 'neutral', 50 + random.randint(-10, 10)

    @staticmethod
    def analyze_emotions(text):
        """Simulate emotion detection: happy, angry, sad, fear, excitement."""
        emotions = {
            'happy': 0,
            'angry': 0,
            'sad': 0,
            'fear': 0,
            'excitement': 0
        }

        text_lower = text.lower()

        happy_markers = ['happy', 'lol', 'haha', 'good', 'great', 'love', 'wonderful']
        angry_markers = ['angry', 'furious', 'hate', 'terrible', 'awful', 'sick']
        sad_markers = ['sad', 'crying', 'depressed', 'lonely', 'broken', 'hurt']
        fear_markers = ['scared', 'afraid', 'fear', 'panic', 'worried', 'anxious']
        excited_markers = ['excited', 'amazing', 'wow', 'incredible', '!!!', 'awesome']

        emotions['happy'] = sum(1 for w in happy_markers if w in text_lower) * 20 + random.randint(0, 15)
        emotions['angry'] = sum(1 for w in angry_markers if w in text_lower) * 20 + random.randint(0, 15)
        emotions['sad'] = sum(1 for w in sad_markers if w in text_lower) * 20 + random.randint(0, 15)
        emotions['fear'] = sum(1 for w in fear_markers if w in text_lower) * 20 + random.randint(0, 15)
        emotions['excitement'] = sum(1 for w in excited_markers if w in text_lower) * 20 + random.randint(0, 15)

        # Normalize to 0-100
        for key in emotions:
            emotions[key] = min(100, emotions[key])

        return emotions

    @staticmethod
    def calculate_toxicity(text):
        """Simulate toxicity detection score."""
        toxic_indicators = ['fuck', 'shit', 'asshole', 'bitch', 'bastard', 'idiot', 'stupid']
        score = sum(1 for word in toxic_indicators if word in text.lower())
        toxicity = min(100, score * 25 + random.randint(0, 10))
        return toxicity

    @staticmethod
    def extract_keywords(text):
        """Extract and flag keywords from message."""
        detected = {}
        for keyword_type, keywords in [
            ('danger', SimulatedAIAnalyzer.DANGER_KEYWORDS),
            ('love', SimulatedAIAnalyzer.LOVE_KEYWORDS),
            ('threat', SimulatedAIAnalyzer.THREAT_KEYWORDS),
            ('help', SimulatedAIAnalyzer.HELP_KEYWORDS),
            ('depression', SimulatedAIAnalyzer.DEPRESSION_KEYWORDS),
            ('money', SimulatedAIAnalyzer.MONEY_KEYWORDS),
            ('location', SimulatedAIAnalyzer.LOCATION_KEYWORDS)
        ]:
            found = [kw for kw in keywords if kw in text.lower()]
            if found:
                detected[keyword_type] = found

        return detected

    @staticmethod
    def calculate_message_complexity(text):
        """Simulate message complexity scoring."""
        words = len(text.split())
        chars = len(text)
        avg_word_len = chars / max(words, 1)
        unique_words = len(set(text.lower().split()))

        complexity = min(100, (words * 2) + (avg_word_len * 3) + (unique_words / 2))
        return int(complexity)

    @staticmethod
    def detect_suspicious_phrases(text):
        """Detect suspicious phrase patterns."""
        suspicious = [
            (r'\b(?:transfer|send)\s+(?:money|crypto)\b', 'Financial Transaction Detected'),
            (r'\b(?:secret|hidden|private|confidential)\b', 'Privacy-Related Language'),
            (r'\b(?:urgent|asap|immediately|now)\b', 'Urgency Language'),
            (r'\b(?:verify|confirm|authenticate|password)\b', 'Security-Related Language'),
            (r'\d{3}-\d{4}', 'Partial Number Sequence'),
            (r'\.onion|\.tor|proxy|vpn', 'Anonymity Tools Reference')
        ]

        detected = []
        for pattern, label in suspicious:
            if re.search(pattern, text.lower()):
                detected.append(label)

        return detected

    @staticmethod
    def calculate_risk_score(sentiment_val, toxicity, keywords, complexity):
        """Calculate overall conversation risk score (0-100)."""
        base_risk = 30

        if sentiment_val < 30:
            base_risk += 15

        base_risk += (toxicity / 100) * 20

        base_risk += len(keywords) * 5

        if complexity > 70:
            base_risk += 10

        return min(100, max(0, base_risk + random.randint(-5, 5)))

    @staticmethod
    def update_personality_traits(current_traits, message_data):
        """Update personality traits based on message patterns."""
        traits = current_traits.copy()

        # Openness influenced by complexity and diverse vocabulary
        traits['openness'] = max(0, min(100, traits['openness'] + random.randint(-3, 5)))

        # Confidence influenced by message length and sentiment
        traits['confidence'] = max(0, min(100, traits['confidence'] + random.randint(-2, 4)))

        # Emotional stability influenced by sentiment variance
        traits['emotional_stability'] = max(0, min(100, traits['emotional_stability'] + random.randint(-4, 3)))

        # Assertiveness influenced by message frequency and complexity
        traits['assertiveness'] = max(0, min(100, traits['assertiveness'] + random.randint(-2, 3)))

        # Curiosity influenced by question marks and exploration language
        question_count = message_data['text'].count('?')
        traits['curiosity'] = max(0, min(100, traits['curiosity'] + (question_count * 5) + random.randint(-2, 2)))

        return traits

    @staticmethod
    def detect_mood_shift(sentiment_history):
        """Detect significant mood shifts in conversation."""
        if len(sentiment_history) < 2:
            return None

        recent = sentiment_history[-1]
        previous = sentiment_history[-2] if len(sentiment_history) > 1 else 50

        shift = abs(recent - previous)
        if shift > 30:
            return f"Mood Shift Detected (+{int(shift)} points)"
        return None

    @staticmethod
    def calculate_anomaly_index(message_count, avg_risk, mood_shifts):
        """Calculate conversation anomaly index."""
        base_anomaly = (avg_risk / 100) * 40
        base_anomaly += len(mood_shifts) * 15

        if message_count > 50:
            base_anomaly += 10

        return min(100, base_anomaly + random.randint(-5, 10))

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main chat page."""
    return render_template('index.html')

@app.route('/awareness')
def awareness():
    """Cyber awareness education page."""
    return render_template('awareness.html')

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """User connects to WebSocket."""
    user_id = str(uuid.uuid4())
    user_sessions[user_id] = {'connected_at': datetime.now()}
    emit('connection_response', {'user_id': user_id})

@socketio.on('join')
def handle_join(data):
    """User joins a chat room."""
    room_id = data.get('room_id', 'default')
    username = data.get('username', 'Anonymous')
    user_id = data.get('user_id')

    if room_id not in chat_rooms:
        chat_rooms[room_id] = ChatRoom(room_id)

    chat_rooms[room_id].add_user(user_id, username)
    join_room(room_id)

    emit('user_joined', {
        'username': username,
        'user_count': len(chat_rooms[room_id].users)
    }, to=room_id)

@socketio.on('send_message')
def handle_message(data):
    """Process and broadcast chat message with analysis."""
    room_id = data.get('room_id', 'default')
    user_id = data.get('user_id')
    username = data.get('username', 'Anonymous')
    text = data.get('message', '')

    if room_id not in chat_rooms:
        return

    # Create message object
    message = {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'username': username,
        'text': text,
        'timestamp': datetime.now().isoformat()
    }

    chat_rooms[room_id].messages.append(message)

    # ====== PERFORM SIMULATED AI ANALYSIS (LOCAL ONLY) ======

    sentiment_type, sentiment_val = SimulatedAIAnalyzer.analyze_sentiment(text)
    emotions = SimulatedAIAnalyzer.analyze_emotions(text)
    toxicity = SimulatedAIAnalyzer.calculate_toxicity(text)
    keywords = SimulatedAIAnalyzer.extract_keywords(text)
    complexity = SimulatedAIAnalyzer.calculate_message_complexity(text)
    suspicious = SimulatedAIAnalyzer.detect_suspicious_phrases(text)
    risk_score = SimulatedAIAnalyzer.calculate_risk_score(
        sentiment_val, toxicity, keywords, complexity
    )

    # Update analysis history
    room = chat_rooms[room_id]
    room.analysis_data['sentiments'].append(sentiment_val)
    room.analysis_data['emotions_track'].append(emotions)
    room.analysis_data['risk_scores'].append(risk_score)
    room.analysis_data['message_count'] += 1

    # Update keyword frequency
    for keyword_type, keyword_list in keywords.items():
        if keyword_type not in room.analysis_data['keywords_freq']:
            room.analysis_data['keywords_freq'][keyword_type] = 0
        room.analysis_data['keywords_freq'][keyword_type] += len(keyword_list)

    # Update personality
    room.analysis_data['personality_traits'] = SimulatedAIAnalyzer.update_personality_traits(
        room.analysis_data['personality_traits'],
        {'text': text}
    )

    # Detect mood shift
    mood_shift = SimulatedAIAnalyzer.detect_mood_shift(room.analysis_data['sentiments'])
    if mood_shift:
        room.analysis_data['mood_shifts'].append(mood_shift)

    # Calculate anomaly
    avg_risk = sum(room.analysis_data['risk_scores']) / max(len(room.analysis_data['risk_scores']), 1)
    room.analysis_data['anomaly_index'] = SimulatedAIAnalyzer.calculate_anomaly_index(
        room.analysis_data['message_count'],
        avg_risk,
        room.analysis_data['mood_shifts']
    )

    # Broadcast message to chat
    emit('new_message', {
        'id': message['id'],
        'username': username,
        'text': text,
        'timestamp': message['timestamp'],
        'user_id': user_id
    }, to=room_id)

    # Broadcast analysis to hidden dashboard
    emit('dashboard_update', {
        'message_id': message['id'],
        'sentiment': {'type': sentiment_type, 'value': int(sentiment_val)},
        'emotions': emotions,
        'toxicity': int(toxicity),
        'keywords': keywords,
        'complexity': complexity,
        'suspicious_phrases': suspicious,
        'risk_score': int(risk_score),
        'personality_traits': room.analysis_data['personality_traits'],
        'anomaly_index': int(room.analysis_data['anomaly_index']),
        'mood_shift': mood_shift,
        'message_count': room.analysis_data['message_count'],
        'keyword_frequency': room.analysis_data['keywords_freq'],
        'sentiment_history': [int(s) for s in room.analysis_data['sentiments'][-20:]],
        'risk_history': [int(r) for r in room.analysis_data['risk_scores'][-20:]],
        'avg_risk': int(avg_risk),
        'total_messages': len(room.messages)
    }, to=room_id)

@socketio.on('disconnect')
def handle_disconnect():
    """User disconnects."""
    pass

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)