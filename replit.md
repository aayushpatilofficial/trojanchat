# TrojanChat - Educational Cyber Awareness Application

## Overview
TrojanChat is an educational cyber awareness application designed to teach users about hidden intelligence systems and digital surveillance. It appears as a simple chat application but contains a hidden AI analysis dashboard (revealed with CTRL+SHIFT+X) that demonstrates how AI systems could theoretically monitor and analyze user communications.

## Purpose
This is an **educational tool only** - designed to raise awareness about:
- How hidden data collection can work in seemingly innocent apps
- AI-powered message analysis capabilities
- The importance of understanding what happens behind the scenes in software

## Key Features

### Chat Interface
- Real-time chat with Socket.IO
- Room-based messaging system
- Clean, modern UI with glassmorphism effects
- Dark/light mode toggle

### Hidden Intelligence Dashboard (CTRL+SHIFT+X)
- **Message Interception**: Shows all messages sent in the room
- **AI Analysis**: Real-time sentiment, emotion, and intent detection
- **AI Thoughts**: Simulated surveillance perspective on messages
- **Conversation Summary**: AI-generated rolling summaries

### Awareness Page
- Educational content about Trojan programs
- How to protect yourself
- Signs of suspicious software

## Tech Stack
- **Backend**: Flask + Flask-SocketIO
- **AI**: OpenAI GPT-4o-mini for message analysis
- **Frontend**: Vanilla JavaScript with Socket.IO client
- **Styling**: Modern CSS with glassmorphism, gradients, animations

## File Structure
```
/
├── main.py                 # Flask server with AI integration
├── templates/
│   ├── index.html          # Main chat interface + dashboard
│   └── awareness.html      # Educational awareness page
└── static/
    ├── style.css           # All styling
    └── chat.js             # Frontend JavaScript
```

## API Routes
- `GET /` - Main chat application
- `GET /awareness` - Educational awareness page
- `GET /health` - Health check endpoint

## WebSocket Events
- `join` - Join a chat room
- `send_message` - Send a message (triggers AI analysis)
- `message` - Receive a message
- `dashboard_update` - Dashboard data with AI insights

## Environment Variables
- `OPENAI_API_KEY` - Required for AI-powered analysis features

## How to Use

### Basic Chat
1. Enter your name and optionally a room ID
2. Click "Join Chat" to enter the room
3. Send messages to other users in the room

### Access Hidden Dashboard
1. Press CTRL+SHIFT+X anywhere in the app
2. The intelligence dashboard slides in from the right
3. View intercepted messages and AI analysis
4. Press CTRL+SHIFT+X again to hide

### Awareness Mode
1. Click the (i) button in the top right
2. Learn about Trojan programs and how to stay safe

## Recent Changes

### November 30, 2025
- Integrated OpenAI GPT-4o-mini for real AI analysis
- Added RealAIAnalyzer class with three AI features:
  - Message analysis (sentiment, emotions, intent, risk assessment)
  - AI thoughts (surveillance perspective simulation)
  - Conversation summaries (rolling AI-generated summaries)
- Updated dashboard HTML with new AI sections
- Added comprehensive error handling for API calls
- Styled new AI sections with glassmorphism effects

## Security Notes
- This is for educational purposes only
- All AI features are opt-in and require API key
- No data is stored permanently
- Messages are only analyzed for educational demonstration
