from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, join_room
import jwt, time, os

SECRET = os.environ.get('SECRET_KEY', 'supersecretkey_demo_change')
PORT = int(os.environ.get('PORT', 5000))

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = SECRET
socketio = SocketIO(app, cors_allowed_origins='*')

WHITELIST = ['ping', 'collect_info', 'show_alert']
clients = {}
audit = []

@app.route('/')
def admin_index():
    return render_template('admin.html')

@app.route('/device')
def device_page():
    return render_template('device.html')

@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.get_json() or {}
    command = data.get('command')
    room = data.get('room', 'all')
    payload = data.get('payload', {})

    if command not in WHITELIST:
        return jsonify({'error': 'command not allowed'}), 400

    cmd_payload = {'command': command, 'payload': payload, 'ts': int(time.time())}
    token = jwt.encode(cmd_payload, SECRET, algorithm='HS256')

    socketio.emit('command', {'command': command, 'payload': payload, 'token': token}, room=room)
    audit.append({'command': command, 'room': room, 'payload': payload, 'ts': time.time()})
    return jsonify({'ok': True, 'issued': cmd_payload})

@app.route('/audit')
def get_audit():
    return jsonify(audit[-200:])

@socketio.on('connect')
def on_connect():
    print('client connected', request.sid)

@socketio.on('register')
def on_register(data):
    device_id = data.get('device_id')
    groups = data.get('groups', [])
    clients[request.sid] = {'device_id': device_id, 'groups': groups}
    for g in groups:
        join_room(g)
    print(f'device registered: {device_id} groups={groups}')

@socketio.on('command_result')
def on_result(data):
    print('result from device:', data)
    audit.append({'result': data, 'ts': time.time()})

@socketio.on('disconnect')
def on_disconnect():
    print('client disconnected', request.sid)
    clients.pop(request.sid, None)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=PORT)
