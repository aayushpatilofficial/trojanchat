from flask import Flask, render_template
from flask_socketio import SocketIO
import os

app = Flask(__name__)
# Use eventlet as async mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

@app.route("/")
def index():
    return render_template("index.html")

# Example SocketIO event
@socketio.on("message")
def handle_message(msg):
    print("Message received:", msg)
    socketio.send(f"You said: {msg}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    socketio.run(app, host="0.0.0.0", port=port)
