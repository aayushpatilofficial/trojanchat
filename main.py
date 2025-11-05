from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO
from gevent import monkey
monkey.patch_all()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

@app.route("/")
def home():
    return "🚀 Flask app running perfectly with Gevent on Render!"

# Example event (keep or replace with your own)
@socketio.on("message")
def handle_message(msg):
    print(f"📩 Received message: {msg}")
    socketio.send(f"Echo: {msg}")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
