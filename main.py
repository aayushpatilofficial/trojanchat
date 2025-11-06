import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

# Store connected clients
connected_clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip': request.remote_addr
    }
    print(f"Client connected: {client_id}")
    emit('connection_response', {
        'data': 'Connected to server',
        'client_count': len(connected_clients)
    })
    socketio.emit('client_count', {'count': len(connected_clients)})

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    print(f"Client disconnected: {client_id}")
    socketio.emit('client_count', {'count': len(connected_clients)})

@socketio.on('send_command')
def handle_command(data):
    command = data.get('command', '').strip()
    sender_id = request.sid

    if not command:
        emit('error', {'message': 'Command cannot be empty'})
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"Command from {sender_id}: {command}")

    emit('command_sent', {
        'command': command,
        'timestamp': timestamp
    })

    socketio.emit('command_received', {
        'command': command,
        'timestamp': timestamp,
        'sender': sender_id[:8]
    }, skip_sid=sender_id)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)