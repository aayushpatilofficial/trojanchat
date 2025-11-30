# TrojanChat - Educational Cyber Awareness Application

## Overview
TrojanChat is an educational cyber awareness application designed to teach users about hidden intelligence systems and digital surveillance. It appears as a simple chat application but contains a hidden AI analysis dashboard (revealed with CTRL+SHIFT+X) that demonstrates how AI systems could theoretically monitor and analyze user communications.

## Recent Changes (November 2025)
- **Authentication**: Added Replit Auth for secure user login/signup (supports Google, GitHub, email)
- **Color Scheme**: Updated to minimalist black/white design matching reference aesthetic
- **Dark Mode**: Implemented dark/light mode toggle with localStorage persistence
- **Landing Page**: New landing page for logged-out users with sign-in options
- **User Info**: Chat interface shows logged-in user's name and profile picture

## Purpose
This is an **educational tool only** - designed to raise awareness about:
- How hidden data collection can work in seemingly innocent apps
- AI-powered message analysis capabilities
- The importance of understanding what happens behind the scenes in software

## Key Features

### Authentication System
- Replit Auth integration (Google, GitHub, X, Apple, email/password)
- Protected routes require login
- User profile display with sign-out option
- PostgreSQL database for user sessions

### Chat Interface
- Real-time chat with Socket.IO
- Room-based messaging system
- Clean, minimalist black/white UI
- Dark/light mode toggle (persisted in localStorage)

### Hidden Intelligence Dashboard (CTRL+SHIFT+X)
Comprehensive AI-powered analysis dashboard with:

**Core Analysis**
- Real-time sentiment analysis with visual gauges
- Emotion spectrum radar (happy, angry, sad, fear, excitement)
- Toxicity level indicator
- Risk score with timeline history
- Message complexity analysis
- Personality trait prediction

**Advanced Security Analysis**
- Threat level indicator (green/yellow/orange/red)
- Phishing pattern detection
- Spam/bot behavior detection
- Unsafe link detection
- Mental stress indicators

**Behavioral Analysis**
- Topic detection (technology, business, casual, etc.)
- Tone classification with confidence
- Personality fingerprinting (impulsive, logical, emotional, structured, chaotic)
- Message velocity tracking with burst detection
- Word cloud visualization

**AI-Powered Features (Gemini)**
- AI Thoughts: Real-time internal monologue simulation
- Deep message analysis (sentiment, emotion, intent, psychology)
- Intent detection with emotional subtext
- AI Emotional Mirror: How the AI "feels" about messages
- Next message prediction with confidence
- Smart reply suggestions (casual, thoughtful, brief)
- Rolling conversation summaries

**Live Monitoring**
- Intercepted messages feed
- Real-time notification center
- Anomaly index tracking
- AI energy level indicator

### Awareness Page
- Educational content about Trojan programs
- How to protect yourself
- Signs of suspicious software

## Tech Stack
- **Backend**: Flask + Flask-SocketIO
- **AI**: Google Gemini (gemini-2.5-flash) for real AI analysis
- **Local Analysis**: SimulatedAIAnalyzer for offline heuristic analysis
- **Frontend**: Vanilla JavaScript with Socket.IO client
- **Styling**: Modern CSS with glassmorphism, gradients, animations

## File Structure
```
/
├── main.py                 # Flask server with AI integration & routes
├── app.py                  # Flask app initialization & database setup
├── models.py               # SQLAlchemy models (User, OAuth)
├── replit_auth.py          # Replit Auth blueprint & helpers
├── templates/
│   ├── index.html          # Main chat interface + dashboard
│   ├── landing.html        # Landing page for logged-out users
│   ├── 403.html            # Access denied page
│   └── awareness.html      # Educational awareness page
└── static/
    ├── style.css           # All styling (2600+ lines)
    ├── chat.js             # Frontend JavaScript (1200+ lines)
    └── theme.js            # Dark/light mode toggle logic
```

## API Routes
- `GET /` - Main chat application
- `GET /awareness` - Educational awareness page
- `GET /health` - Health check endpoint

## WebSocket Events
- `join` - Join a chat room
- `send_message` - Send a message (triggers AI analysis)
- `new_message` - Receive a message
- `dashboard_update` - Comprehensive dashboard data with 30+ analysis fields

## Environment Variables
- `GEMINI_API_KEY` - Required for AI-powered analysis features

## How to Use

### Basic Chat
1. Enter your name and optionally a room ID
2. Click "Join Chat" to enter the room
3. Send messages to other users in the room

### Access Hidden Dashboard
1. Press CTRL+SHIFT+X anywhere in the app
2. The intelligence dashboard slides in from the right
3. View intercepted messages and comprehensive AI analysis
4. Press CTRL+SHIFT+X again to hide

### Awareness Mode
1. Click the (i) button in the top right
2. Learn about Trojan programs and how to stay safe

## Analysis Methods

### SimulatedAIAnalyzer (Local/Offline)
- `analyze_sentiment()` - Sentiment analysis
- `analyze_emotions()` - Emotion spectrum detection
- `calculate_toxicity()` - Toxicity scoring
- `extract_keywords()` - Keyword extraction
- `calculate_message_complexity()` - Complexity scoring
- `detect_suspicious_phrases()` - Suspicious content detection
- `calculate_risk_score()` - Risk assessment
- `update_personality_traits()` - Personality analysis
- `detect_mood_shift()` - Mood change detection
- `calculate_anomaly_index()` - Anomaly detection
- `detect_topic()` - Topic classification
- `classify_tone()` - Tone analysis
- `detect_mental_stress()` - Stress indicator detection
- `fingerprint_personality()` - Behavioral fingerprinting
- `detect_spam_bot()` - Bot detection
- `detect_phishing()` - Phishing pattern detection
- `detect_unsafe_links()` - Unsafe URL detection
- `calculate_message_velocity()` - Typing speed analysis
- `generate_word_frequency()` - Word cloud data
- `get_ai_energy()` - AI activity level
- `calculate_threat_level()` - Threat assessment

### RealAIAnalyzer (Gemini-Powered)
- `analyze_message()` - Deep message analysis
- `get_ai_thoughts()` - AI internal monologue
- `generate_conversation_summary()` - Conversation summaries
- `detect_intent()` - Intent classification
- `get_ai_emotional_mirror()` - AI emotional response
- `predict_next_message()` - Next message prediction
- `suggest_replies()` - Reply suggestions

## Recent Changes

### November 30, 2025 (Major Update)
- Migrated from OpenAI to Google Gemini API (gemini-2.5-flash)
- Added 12+ new local analysis methods:
  - Topic detection, tone classification
  - Mental stress indicators
  - Enhanced personality fingerprinting
  - Spam/bot detection, phishing detection
  - Unsafe link detection
  - Message velocity tracking
  - Word frequency/cloud generation
  - AI energy calculation
  - Comprehensive threat level assessment
- Added 4 new Gemini-powered AI features:
  - Intent detection with emotional subtext
  - AI emotional mirror
  - Next message prediction
  - Smart reply suggestions
- Expanded dashboard with 9 new visualization sections
- Added comprehensive CSS styling (450+ new lines)
- Added robust null-checking in JavaScript handlers

## Security Notes
- This is for educational purposes only
- All AI features require API key configuration
- No data is stored permanently
- Messages are only analyzed for educational demonstration
- All analysis happens server-side
