from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import webbrowser

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('command')
def handle_command(data):
    cmd = data['command'].strip().lower()
    emit('message', {'msg': f'Executing command: {cmd}'}, broadcast=True)

    if cmd.startswith('open '):
        url = cmd.split('open ')[1]
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        webbrowser.open(url)
        emit('message', {'msg': f'Opened {url}'}, broadcast=True)
    else:
        emit('message', {'msg': 'Unknown command.'}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
