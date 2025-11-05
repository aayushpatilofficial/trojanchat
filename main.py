from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import os
from openai import OpenAI
import google.generativeai as genai
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load API keys from environment variables (set these in Replit Secrets)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize Gemini model
gemini_model = genai.GenerativeModel("gemini-pro")

@app.route('/')
def index():
    return render_template("index.html")

@socketio.on("start_conversation")
def handle_conversation():
    socketio.start_background_task(ai_conversation_loop)

def ai_conversation_loop():
    ai_a_message = "Hello, who are you?"
    socketio.emit("neural_pulse", {"from": "A", "text": ai_a_message})
    time.sleep(3)

    for i in range(5):
        # AI B (Gemini)
        gemini_response = gemini_model.generate_content(ai_a_message)
        ai_b_message = gemini_response.text.strip()
        socketio.emit("neural_pulse", {"from": "B", "text": ai_b_message})
        time.sleep(3)

        # AI A (OpenAI) - using new v2 syntax
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[{"role": "user", "content": ai_b_message}]
        )
        ai_a_message = response.choices[0].message.content.strip()
        socketio.emit("neural_pulse", {"from": "A", "text": ai_a_message})
        time.sleep(3)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
