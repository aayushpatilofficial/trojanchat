import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
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
BROADCAST_ROOM = 'broadcast_room'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@socketio.on('connect')
def on_connect():
    client_id = request.sid
    connected_clients[client_id] = True
    join_room(BROADCAST_ROOM)
    total = len(connected_clients)

    print(f'✓ Client connected: {client_id} | Total: {total}')

    # Notify connecting client
    emit('connection_response', {'message': 'Connected to server'})

    # Broadcast to ALL clients in room
    socketio.emit('client_count', {'count': total}, room=BROADCAST_ROOM)

@socketio.on('disconnect')
def on_disconnect():
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    leave_room(BROADCAST_ROOM)
    total = len(connected_clients)

    print(f'✗ Client disconnected: {client_id} | Total: {total}')

    # Notify all remaining clients
    if connected_clients:
        socketio.emit('client_count', {'count': total}, room=BROADCAST_ROOM)

@socketio.on('send_command')
def on_command(data):
    try:
        command = data.get('command', '').strip()
        sender_id = request.sid
        timestamp = datetime.now().strftime('%H:%M:%S')

        if not command:
            print('⚠️ Empty command received')
            return

        print(f'📤 Command received: {command}')
        print(f'   Sender: {sender_id}')
        print(f'   Total clients: {len(connected_clients)}')

        # Send to SENDER too (so they see it execute)
        socketio.emit('command_received', {
            'command': command,
            'timestamp': timestamp,
            'sender': sender_id[:6]
        }, room=sender_id)
        print(f'   ✓ Sent to sender')

        # Send to each OTHER client
        for client_id in connected_clients.keys():
            if client_id != sender_id:
                print(f'   → Sending to client: {client_id}')
                socketio.emit('command_received', {
                    'command': command,
                    'timestamp': timestamp,
                    'sender': sender_id[:6]
                }, room=client_id)

        print(f'   ✓ Sent to all other clients')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Starting server on port {port}...')
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)