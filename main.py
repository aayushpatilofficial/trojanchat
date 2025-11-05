from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from gevent import monkey
import requests

monkey.patch_all()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("command")
def handle_command(cmd):
    print(f"📡 Command received: {cmd}")
    emit("broadcast", cmd, broadcast=True)

@app.route("/proxy")
def proxy():
    url = request.args.get("url")
    if not url:
        return "No URL provided", 400
    try:
        if not url.startswith("http"):
            url = "https://" + url
        r = requests.get(url)
        return r.text
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
