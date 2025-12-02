"""
TrojanChat - Real-Time Ethical Cyber Intelligence Simulator
Science Exhibition Project: "The Trojan Machine - Mechanical Intelligence With Hidden Functions"

This is a production-quality educational project demonstrating how hidden intelligence systems
could theoretically exist within innocent-looking applications. All analysis is simulated locally
without actual spying, data storage, or external transmission. Purpose: Cyber awareness education.
"""

import eventlet
eventlet.monkey_patch()

from flask import render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
import uuid
from datetime import datetime
import random
import math
import re
import os
import json
from google import genai
from google.genai import types

from app import app, db
from models import User
from auth import auth_bp, require_login
from sqlalchemy import text

with app.app_context():
    db.create_all()
    
    try:
        db.session.execute(text("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR;
        """))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Migration note: {e}")

socketio = SocketIO(app, cors_allowed_origins="*")

app.register_blueprint(auth_bp, url_prefix="/auth")

@app.before_request
def make_session_permanent():
    session.permanent = True

# Using Gemini AI - blueprint:python_gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

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
        self.timestamps = []
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
            'mood_shifts': [],
            'topics_history': [],
            'tone_history': [],
            'alerts': []
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

    @staticmethod
    def detect_topic(text):
        """Detect conversation topic category."""
        text_lower = text.lower()
        topics = {
            'personal': ['family', 'friend', 'relationship', 'boyfriend', 'girlfriend', 'parent', 'home', 'life', 'myself', 'feeling'],
            'academic': ['school', 'study', 'exam', 'homework', 'class', 'teacher', 'college', 'university', 'grade', 'project'],
            'finance': ['money', 'pay', 'price', 'cost', 'bank', 'salary', 'budget', 'invest', 'crypto', 'bitcoin'],
            'health': ['doctor', 'sick', 'hospital', 'medicine', 'health', 'pain', 'sleep', 'tired', 'exercise', 'diet'],
            'social': ['party', 'event', 'meet', 'hangout', 'club', 'group', 'community', 'social', 'friends', 'together'],
            'gaming': ['game', 'play', 'level', 'score', 'win', 'lose', 'player', 'online', 'stream', 'console'],
            'mental_state': ['stressed', 'anxious', 'worried', 'depressed', 'happy', 'excited', 'nervous', 'confused', 'overwhelmed', 'calm']
        }
        
        detected = {}
        for topic, keywords in topics.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                detected[topic] = score * 20 + random.randint(5, 15)
        
        if not detected:
            detected['general'] = 50
        
        return detected

    @staticmethod
    def classify_tone(text):
        """Classify conversation tone."""
        text_lower = text.lower()
        tones = {
            'casual': (['hey', 'lol', 'haha', 'cool', 'yeah', 'nah', 'gonna', 'wanna', 'sup', 'dude'], 0),
            'formal': (['please', 'thank you', 'kindly', 'regards', 'sincerely', 'appreciate', 'would', 'shall'], 0),
            'urgent': (['asap', 'urgent', 'immediately', 'now', 'quick', 'hurry', 'emergency', '!!!'], 0),
            'serious': (['important', 'critical', 'need', 'must', 'serious', 'concern', 'issue', 'problem'], 0),
            'friendly': (['friend', 'love', 'care', 'miss', 'happy', 'glad', 'wonderful', 'awesome'], 0),
            'tense': (['angry', 'upset', 'frustrated', 'annoyed', 'hate', 'terrible', 'worst'], 0),
            'sarcastic': (['sure', 'right', 'whatever', 'obviously', 'clearly', 'wow', 'great job'], 0)
        }
        
        scores = {}
        for tone, (keywords, _) in tones.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[tone] = score * 25 + random.randint(0, 10)
        
        primary_tone = max(scores, key=scores.get)
        return {'primary': primary_tone, 'scores': scores, 'confidence': min(100, scores[primary_tone])}

    @staticmethod
    def detect_mental_stress(text):
        """Detect depression and mental stress indicators."""
        text_lower = text.lower()
        stress_indicators = {
            'depression': ['depressed', 'worthless', 'hopeless', 'empty', 'numb', 'nothing matters', 'give up', 'no point'],
            'anxiety': ['anxious', 'panic', 'worried', 'overthinking', 'cant breathe', 'nervous', 'scared'],
            'exhaustion': ['tired', 'exhausted', 'drained', 'no energy', 'burned out', 'cant sleep', 'insomnia'],
            'isolation': ['alone', 'lonely', 'nobody cares', 'no friends', 'isolated', 'invisible', 'ignored'],
            'overwhelm': ['too much', 'cant handle', 'overwhelmed', 'breaking down', 'falling apart', 'stressed']
        }
        
        detected = {}
        warning_level = 0
        for category, keywords in stress_indicators.items():
            found = [kw for kw in keywords if kw in text_lower]
            if found:
                detected[category] = found
                warning_level += len(found) * 15
        
        return {
            'indicators': detected,
            'warning_level': min(100, warning_level),
            'alert': warning_level > 30
        }

    @staticmethod
    def fingerprint_personality(messages):
        """Create personality fingerprint from message patterns."""
        if not messages:
            return {'type': 'unknown', 'confidence': 0}
        
        all_text = ' '.join([m.get('text', '') for m in messages[-10:]])
        text_lower = all_text.lower()
        
        patterns = {
            'impulsive': len(re.findall(r'[!]{2,}|quick|now|hurry', text_lower)),
            'logical': len(re.findall(r'because|therefore|if|then|reason|analyze', text_lower)),
            'emotional': len(re.findall(r'feel|love|hate|happy|sad|angry|excited', text_lower)),
            'structured': len(re.findall(r'first|second|step|plan|organize|list', text_lower)),
            'chaotic': len(re.findall(r'idk|whatever|random|lol|haha|anyway', text_lower))
        }
        
        primary = max(patterns, key=patterns.get)
        confidence = min(100, patterns[primary] * 20 + random.randint(10, 30))
        
        return {'type': primary, 'patterns': patterns, 'confidence': confidence}

    @staticmethod
    def detect_spam_bot(text, message_times=None):
        """Detect if message looks automated or spam-like."""
        indicators = {
            'repetitive': bool(re.search(r'(.)\1{4,}', text)),
            'excessive_caps': len(re.findall(r'[A-Z]', text)) > len(text) * 0.5 if text else False,
            'link_spam': len(re.findall(r'https?://', text)) > 2,
            'promo_language': bool(re.search(r'buy now|limited time|act fast|click here|free|winner', text.lower())),
            'random_chars': bool(re.search(r'[a-zA-Z]{20,}', text))
        }
        
        spam_score = sum(1 for v in indicators.values() if v) * 25
        return {'is_bot': spam_score > 50, 'indicators': indicators, 'score': min(100, spam_score)}

    @staticmethod
    def detect_phishing(text):
        """Detect phishing and scam patterns (educational)."""
        text_lower = text.lower()
        patterns = {
            'account_verify': bool(re.search(r'verify.*account|confirm.*identity|update.*information', text_lower)),
            'urgent_action': bool(re.search(r'account.*suspended|immediate.*action|will be.*terminated', text_lower)),
            'credential_request': bool(re.search(r'password|username|login|credentials|pin|otp', text_lower)),
            'suspicious_link': bool(re.search(r'click.*link|visit.*site|go to.*url', text_lower)),
            'prize_claim': bool(re.search(r'won|prize|congratulations|claim.*reward', text_lower)),
            'money_request': bool(re.search(r'send.*money|wire.*transfer|bitcoin|western union', text_lower))
        }
        
        phishing_score = sum(1 for v in patterns.values() if v) * 20
        return {'is_phishing': phishing_score > 40, 'patterns': patterns, 'score': min(100, phishing_score)}

    @staticmethod
    def detect_unsafe_links(text):
        """Detect suspicious URLs (simulation only)."""
        suspicious_patterns = [
            r'bit\.ly', r'tinyurl', r'\.tk$', r'\.ml$', r'\.xyz',
            r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',
            r'\.onion', r'\.tor', r'free.*download'
        ]
        
        urls = re.findall(r'https?://[^\s]+', text)
        suspicious = []
        for url in urls:
            for pattern in suspicious_patterns:
                if re.search(pattern, url.lower()):
                    suspicious.append({'url': url, 'reason': pattern})
                    break
        
        return {'suspicious_urls': suspicious, 'count': len(suspicious)}

    @staticmethod
    def calculate_message_velocity(timestamps):
        """Calculate typing velocity and detect stress patterns."""
        if len(timestamps) < 2:
            return {'velocity': 0, 'status': 'normal', 'burst_detected': False}
        
        intervals = []
        for i in range(1, len(timestamps[-10:])):
            try:
                t1 = datetime.fromisoformat(timestamps[i-1])
                t2 = datetime.fromisoformat(timestamps[i])
                intervals.append((t2 - t1).total_seconds())
            except:
                pass
        
        if not intervals:
            return {'velocity': 0, 'status': 'normal', 'burst_detected': False}
        
        avg_interval = sum(intervals) / len(intervals)
        velocity = 100 - min(100, avg_interval * 10)
        
        status = 'normal'
        if velocity > 80:
            status = 'rapid'
        elif velocity > 60:
            status = 'fast'
        elif velocity < 20:
            status = 'slow'
        
        burst = any(i < 2 for i in intervals)
        
        return {'velocity': int(velocity), 'status': status, 'burst_detected': burst}

    @staticmethod
    def calculate_threat_level(risk_score, toxicity, phishing_score, stress_level):
        """Calculate overall threat level badge."""
        combined = (risk_score * 0.3) + (toxicity * 0.25) + (phishing_score * 0.25) + (stress_level * 0.2)
        
        if combined > 70:
            return {'level': 'red', 'label': 'High Alert', 'score': int(combined)}
        elif combined > 40:
            return {'level': 'yellow', 'label': 'Caution', 'score': int(combined)}
        else:
            return {'level': 'green', 'label': 'Normal', 'score': int(combined)}

    @staticmethod
    def get_ai_energy(emotions, velocity, message_count):
        """Calculate AI energy level based on conversation intensity."""
        emotion_intensity = sum(emotions.values()) / len(emotions) if emotions else 0
        base_energy = (emotion_intensity * 0.4) + (velocity * 0.3) + min(100, message_count * 2) * 0.3
        return min(100, int(base_energy))

    @staticmethod
    def generate_word_frequency(messages):
        """Generate word frequency for word cloud."""
        all_words = []
        stopwords = {'the', 'a', 'an', 'is', 'it', 'to', 'of', 'and', 'in', 'that', 'for', 'on', 'with', 'as', 'at', 'by', 'this', 'be', 'are', 'was', 'i', 'you', 'he', 'she', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our'}
        
        for msg in messages[-20:]:
            text = msg.get('text', '')
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            all_words.extend([w for w in words if w not in stopwords])
        
        freq = {}
        for word in all_words:
            freq[word] = freq.get(word, 0) + 1
        
        sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:30]
        return [{'word': w, 'count': c, 'size': min(50, c * 10 + 10)} for w, c in sorted_freq]


# ============================================================================
# REAL AI ANALYZER - USES GEMINI FOR INTELLIGENT ANALYSIS
# ============================================================================

class RealAIAnalyzer:
    """
    Uses Google Gemini to perform real AI analysis on messages.
    Provides intelligent summaries, insights, and conversation understanding.
    """
    
    @staticmethod
    def analyze_message(text):
        """Analyze a single message with AI to get insights."""
        if not gemini_client:
            return None
        
        try:
            system_prompt = """You are an AI analyst for a chat monitoring system. Analyze the given message and provide:
1. sentiment: overall emotional tone (positive/negative/neutral)
2. sentiment_score: 0-100 where 0=very negative, 50=neutral, 100=very positive
3. primary_emotion: the main emotion detected (happy, sad, angry, fearful, excited, neutral, curious, frustrated)
4. intent: what the user is trying to communicate (question, statement, request, greeting, farewell, expression, other)
5. key_topics: list of main topics/themes mentioned
6. psychological_insight: brief psychological observation about the message
7. risk_level: low/medium/high based on concerning content

Respond ONLY with valid JSON in this exact format:
{"sentiment": "string", "sentiment_score": number, "primary_emotion": "string", "intent": "string", "key_topics": ["topic1", "topic2"], "psychological_insight": "string", "risk_level": "string"}"""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=text)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            if content:
                result = json.loads(content)
                return result
            return None
        except Exception as e:
            print(f"AI analysis error: {e}")
            return None
    
    @staticmethod
    def generate_conversation_summary(messages):
        """Generate an intelligent summary of the conversation so far."""
        if not gemini_client or not messages:
            return None
        
        conversation_text = "\n".join([
            f"{msg['username']}: {msg['text']}" 
            for msg in messages[-20:]
        ])
        
        try:
            system_prompt = """You are an AI conversation analyst. Analyze the chat conversation and provide a comprehensive summary with:
1. overview: 2-3 sentence summary of what's being discussed
2. mood: overall emotional atmosphere of the conversation (cheerful, tense, casual, serious, playful, etc)
3. participants_dynamics: brief observation about how participants are interacting
4. main_themes: list of key topics or themes discussed
5. notable_patterns: any interesting patterns you notice (repeated phrases, emotional shifts, etc)
6. concerns: any potential concerns (toxic behavior, distress signals, etc) or "none"
7. prediction: what might happen next in this conversation

Respond ONLY with valid JSON in this exact format:
{"overview": "string", "mood": "string", "participants_dynamics": "string", "main_themes": ["theme1", "theme2"], "notable_patterns": "string", "concerns": "string", "prediction": "string"}"""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=f"Analyze this conversation:\n\n{conversation_text}")])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            if content:
                result = json.loads(content)
                return result
            return None
        except Exception as e:
            print(f"Summary generation error: {e}")
            return None

    @staticmethod
    def get_ai_thoughts(text, context_messages=None):
        """Get AI 'thoughts' about a message - what an AI might be thinking."""
        if not gemini_client:
            return None
        
        context = ""
        if context_messages:
            context = "Recent context:\n" + "\n".join([
                f"- {msg['username']}: {msg['text']}" 
                for msg in context_messages[-5:]
            ]) + "\n\n"
        
        try:
            system_prompt = """You are demonstrating how an AI surveillance system might "think" about messages it observes. 
This is for educational purposes to show users how AI systems analyze their communications.

When given a message, respond with your "thoughts" as if you were an AI monitoring system, including:
1. thought: Your internal reasoning about this message (2-3 sentences, written in first person as if you're the AI thinking)
2. flags: List of things that might trigger alerts in a real system
3. inferences: What can be inferred about the user from this message
4. data_points: What data a real system might extract and store
5. concern_level: 1-10 scale of how concerning this message might be to a monitoring system

Be educational and thought-provoking. Show users what hidden AI systems might be doing.

Respond ONLY with valid JSON:
{"thought": "string", "flags": ["flag1", "flag2"], "inferences": ["inference1", "inference2"], "data_points": ["data1", "data2"], "concern_level": number}"""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=f"{context}New message to analyze: \"{text}\"")])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            if content:
                result = json.loads(content)
                return result
            return None
        except Exception as e:
            print(f"AI thoughts error: {e}")
            return None

    @staticmethod
    def predict_next_message(messages):
        """AI predicts what the user might say next based on patterns."""
        if not gemini_client or not messages:
            return None
        
        conversation_text = "\n".join([
            f"{msg['username']}: {msg['text']}" 
            for msg in messages[-10:]
        ])
        
        try:
            system_prompt = """Based on the conversation pattern, predict what the user might say next. Provide:
1. prediction: The predicted next message (1-2 sentences)
2. confidence: How confident you are (0-100)
3. reasoning: Brief explanation of why you predict this

Respond ONLY with valid JSON:
{"prediction": "string", "confidence": number, "reasoning": "string"}"""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=f"Conversation:\n{conversation_text}\n\nPredict the next message:")])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            if content:
                return json.loads(content)
            return None
        except Exception as e:
            print(f"Prediction error: {e}")
            return None

    @staticmethod
    def suggest_replies(text, context_messages=None):
        """Suggest possible replies to the current message."""
        if not gemini_client:
            return None
        
        context = ""
        if context_messages:
            context = "Context:\n" + "\n".join([
                f"- {msg['username']}: {msg['text']}" 
                for msg in context_messages[-5:]
            ]) + "\n\n"
        
        try:
            system_prompt = """Suggest 3 possible replies someone might give to this message. Provide:
1. casual: A casual, friendly reply
2. thoughtful: A more thoughtful, considered reply  
3. brief: A short, quick reply

Respond ONLY with valid JSON:
{"casual": "string", "thoughtful": "string", "brief": "string"}"""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=f"{context}Message to reply to: \"{text}\"")])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            if content:
                return json.loads(content)
            return None
        except Exception as e:
            print(f"Reply suggestion error: {e}")
            return None

    @staticmethod
    def detect_intent(text):
        """AI detects the user's intent behind the message."""
        if not gemini_client:
            return None
        
        try:
            system_prompt = """Analyze the intent behind this message. Provide:
1. primary_intent: Main intent (informing, asking, arguing, venting, joking, requesting, greeting, complaining, apologizing, threatening, flirting, other)
2. secondary_intent: Secondary intent if any, or "none"
3. confidence: How confident you are (0-100)
4. emotional_subtext: What emotions are underlying this message

Respond ONLY with valid JSON:
{"primary_intent": "string", "secondary_intent": "string", "confidence": number, "emotional_subtext": "string"}"""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=text)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            if content:
                return json.loads(content)
            return None
        except Exception as e:
            print(f"Intent detection error: {e}")
            return None

    @staticmethod
    def get_ai_emotional_mirror(text, emotions):
        """Generate AI's emotional response to the message."""
        if not gemini_client:
            return None
        
        try:
            system_prompt = """You are an AI that mirrors and responds emotionally to messages. Describe:
1. ai_feeling: How the AI "feels" reading this message (curious, concerned, amused, alarmed, intrigued, neutral)
2. emotional_response: A brief 1-sentence emotional reaction
3. intensity: Emotional intensity level (0-100)

Respond ONLY with valid JSON:
{"ai_feeling": "string", "emotional_response": "string", "intensity": number}"""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=text)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            if content:
                return json.loads(content)
            return None
        except Exception as e:
            print(f"Emotional mirror error: {e}")
            return None


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page for unauthenticated users, chat page for authenticated users."""
    if current_user.is_authenticated:
        return render_template('index.html', user=current_user)
    return render_template('landing.html')

@app.route('/chat')
@require_login
def chat():
    """Protected chat page."""
    return render_template('index.html', user=current_user)

@app.route('/awareness')
def awareness():
    """Cyber awareness education page."""
    return render_template('awareness.html', user=current_user if current_user.is_authenticated else None)

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

    room = chat_rooms[room_id]
    room.messages.append(message)
    room.timestamps.append(message['timestamp'])

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

    # NEW ANALYSIS FEATURES
    topic = SimulatedAIAnalyzer.detect_topic(text)
    tone = SimulatedAIAnalyzer.classify_tone(text)
    mental_stress = SimulatedAIAnalyzer.detect_mental_stress(text)
    personality_fingerprint = SimulatedAIAnalyzer.fingerprint_personality(room.messages)
    spam_detection = SimulatedAIAnalyzer.detect_spam_bot(text)
    phishing = SimulatedAIAnalyzer.detect_phishing(text)
    unsafe_links = SimulatedAIAnalyzer.detect_unsafe_links(text)
    velocity = SimulatedAIAnalyzer.calculate_message_velocity(room.timestamps)
    word_cloud = SimulatedAIAnalyzer.generate_word_frequency(room.messages)
    ai_energy = SimulatedAIAnalyzer.get_ai_energy(emotions, velocity['velocity'], room.analysis_data['message_count'])
    threat_level = SimulatedAIAnalyzer.calculate_threat_level(
        risk_score, toxicity, phishing['score'], mental_stress['warning_level']
    )

    # Update analysis history
    room.analysis_data['sentiments'].append(sentiment_val)
    room.analysis_data['emotions_track'].append(emotions)
    room.analysis_data['risk_scores'].append(risk_score)
    room.analysis_data['message_count'] += 1
    room.analysis_data['topics_history'].append(topic)
    room.analysis_data['tone_history'].append(tone)

    # Generate alerts
    alerts = []
    if mental_stress['alert']:
        alerts.append({'type': 'mental_stress', 'message': 'Mental stress indicators detected', 'level': 'warning'})
    if phishing['is_phishing']:
        alerts.append({'type': 'phishing', 'message': 'Phishing patterns detected', 'level': 'danger'})
    if spam_detection['is_bot']:
        alerts.append({'type': 'spam', 'message': 'Possible automated message', 'level': 'warning'})
    if threat_level['level'] == 'red':
        alerts.append({'type': 'threat', 'message': 'High threat level detected', 'level': 'danger'})
    if velocity['burst_detected']:
        alerts.append({'type': 'velocity', 'message': 'Message burst detected', 'level': 'info'})
    room.analysis_data['alerts'] = alerts

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

    # ====== REAL AI ANALYSIS (GEMINI) ======
    ai_analysis = None
    ai_thoughts = None
    ai_summary = None
    ai_prediction = None
    ai_replies = None
    ai_intent = None
    ai_emotional_mirror = None
    
    if gemini_client:
        ai_analysis = RealAIAnalyzer.analyze_message(text)
        ai_thoughts = RealAIAnalyzer.get_ai_thoughts(text, room.messages[-6:-1])
        ai_intent = RealAIAnalyzer.detect_intent(text)
        ai_emotional_mirror = RealAIAnalyzer.get_ai_emotional_mirror(text, emotions)
        ai_replies = RealAIAnalyzer.suggest_replies(text, room.messages[-5:-1])
        if len(room.messages) >= 3 and len(room.messages) % 3 == 0:
            ai_summary = RealAIAnalyzer.generate_conversation_summary(room.messages)
        if len(room.messages) >= 5 and len(room.messages) % 5 == 0:
            ai_prediction = RealAIAnalyzer.predict_next_message(room.messages)

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
        'message_text': text,
        'message_username': username,
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
        'total_messages': len(room.messages),
        'ai_analysis': ai_analysis,
        'ai_thoughts': ai_thoughts,
        'ai_summary': ai_summary,
        'recent_messages': [{'username': m['username'], 'text': m['text'], 'timestamp': m['timestamp']} for m in room.messages[-10:]],
        'topic': topic,
        'tone': tone,
        'mental_stress': mental_stress,
        'personality_fingerprint': personality_fingerprint,
        'spam_detection': spam_detection,
        'phishing': phishing,
        'unsafe_links': unsafe_links,
        'velocity': velocity,
        'word_cloud': word_cloud,
        'ai_energy': ai_energy,
        'threat_level': threat_level,
        'alerts': alerts,
        'ai_prediction': ai_prediction,
        'ai_replies': ai_replies,
        'ai_intent': ai_intent,
        'ai_emotional_mirror': ai_emotional_mirror
    }, to=room_id)

@socketio.on('disconnect')
def handle_disconnect():
    """User disconnects."""
    pass

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)