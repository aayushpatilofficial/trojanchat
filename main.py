import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'render-secret-key-2024'

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25
)

connected_clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@socketio.on('connect')
def on_connect(auth):
    client_id = request.sid
    connected_clients[client_id] = True
    total = len(connected_clients)

    print(f'✓ Client connected: {client_id} | Total: {total}')

    # Notify connecting client
    emit('connection_response', {'message': 'Connected to server'})

    # Send to ALL clients using socketio.emit (works with eventlet)
    for cid in connected_clients.keys():
        socketio.emit('client_count', {'count': total}, to=cid)

@socketio.on('disconnect')
def on_disconnect(auth):
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    total = len(connected_clients)

    print(f'✗ Client disconnected: {client_id} | Total: {total}')

    # Notify all remaining clients
    for cid in connected_clients.keys():
        socketio.emit('client_count', {'count': total}, to=cid)

@socketio.on('send_command')
def on_command(data, auth):
    try:
        command = data.get('command', '').strip()
        sender_id = request.sid
        timestamp = datetime.now().strftime('%H:%M:%S')

        if not command:
            return

        print(f'📤 Command: {command}')

        # Confirm to sender
        emit('command_sent', {
            'command': command,
            'timestamp': timestamp
        })

        # Send to all OTHER clients
        for cid in connected_clients.keys():
            if cid != sender_id:
                socketio.emit('command_received', {
                    'command': command,
                    'timestamp': timestamp,
                    'sender': sender_id[:6]
                }, to=cid)
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Starting server on port {port}...')
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)