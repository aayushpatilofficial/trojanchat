import os
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import jwt
except ImportError:
    jwt = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'neura-sync-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///neura_sync.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ==================== DATABASE MODELS ====================

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sessions = db.relationship('Session', backref='user', cascade='all, delete-orphan')
    clipboard_items = db.relationship('ClipboardItem', backref='user', cascade='all, delete-orphan')
    commands = db.relationship('CommandLog', backref='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Session(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    tabs = db.Column(db.JSON, default=list)
    tab_count = db.Column(db.Integer, default=0)
    size_mb = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_auto_saved = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'tabs': self.tabs,
            'tab_count': self.tab_count,
            'size_mb': self.size_mb,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_auto_saved': self.is_auto_saved
        }

class ClipboardItem(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(50), default='text')
    size_kb = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'content_type': self.content_type,
            'size_kb': self.size_kb,
            'created_at': self.created_at.isoformat(),
            'full_content': self.content
        }

class CommandLog(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    command = db.Column(db.String(255), nullable=False)
    command_type = db.Column(db.String(50))
    device_count = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='sent')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'command': self.command,
            'command_type': self.command_type,
            'device_count': self.device_count,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class ProductivityLog(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    focus_score = db.Column(db.Integer, default=50)
    time_on_task = db.Column(db.Integer, default=0)
    distractions = db.Column(db.Integer, default=0)
    pomodoro_completed = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'focus_score': self.focus_score,
            'time_on_task': self.time_on_task,
            'distractions': self.distractions,
            'pomodoro_completed': self.pomodoro_completed,
            'created_at': self.created_at.isoformat()
        }

# ==================== WEBSOCKET EVENTS ====================

connected_clients = {}

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.utcnow(),
        'user_id': None
    }
    print(f'✓ Client connected: {client_id} | Total: {len(connected_clients)}')
    emit('connection_response', {'message': 'Connected', 'client_id': client_id})
    socketio.emit('client_count', {'count': len(connected_clients)})

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    print(f'✗ Client disconnected: {client_id} | Total: {len(connected_clients)}')
    socketio.emit('client_count', {'count': len(connected_clients)})

@socketio.on('send_command')
def handle_command(data):
    try:
        command = data.get('command', '').strip()
        user_id = data.get('user_id', 'anonymous')
        sender_id = request.sid

        if not command:
            emit('error', {'message': 'Empty command'})
            return

        cmd_type = 'open' if command.startswith('open') else 'search' if command.startswith('search') else 'unknown'

        # Parse command details
        cmd_details = {}
        if cmd_type == 'open':
            url = command.replace('open ', '').strip()
            cmd_details = {'type': 'open', 'url': url}
        elif cmd_type == 'search':
            query = command.replace('search ', '').strip()
            cmd_details = {'type': 'search', 'query': query}

        # Log command to database (optional, handle if DB not ready)
        try:
            cmd_log = CommandLog(
                user_id=user_id if user_id else 'guest',
                command=command,
                command_type=cmd_type,
                device_count=len(connected_clients),
                status='executing'
            )
            db.session.add(cmd_log)
            db.session.commit()
            cmd_id = cmd_log.id
        except:
            cmd_id = str(uuid.uuid4())

        timestamp = datetime.utcnow().isoformat()

        # Prepare command payload
        payload = {
            'command': command,
            'cmd_type': cmd_type,
            'details': cmd_details,
            'timestamp': timestamp,
            'sender': sender_id[:8],
            'command_id': cmd_id,
            'status': 'executing',
            'device_count': len(connected_clients)
        }

        print(f'📤 Broadcasting command: {command} to {len(connected_clients)} clients')

        # Broadcast to ALL clients (including sender)
        socketio.emit('command_received', payload)

        # Send acknowledgment to sender
        emit('command_ack', {
            'status': 'success',
            'command_id': cmd_id,
            'message': f'Command sent to {len(connected_clients)} device(s)',
            'total_clients': len(connected_clients)
        })

        print(f'✓ Command broadcast complete: {command} ({len(connected_clients)} devices)')

    except Exception as e:
        print(f'❌ Command Error: {e}')
        emit('error', {'message': str(e)})

@socketio.on('sync_clipboard')
def handle_clipboard_sync(data):
    try:
        user_id = data.get('user_id')
        content = data.get('content')

        if not content:
            emit('error', {'message': 'Empty clipboard'})
            return

        clipboard_item = ClipboardItem(
            user_id=user_id,
            content=content,
            content_type=data.get('content_type', 'text'),
            size_kb=len(content.encode()) / 1024
        )
        db.session.add(clipboard_item)
        db.session.commit()

        socketio.emit('clipboard_updated', {
            'item': clipboard_item.to_dict(),
            'total_items': ClipboardItem.query.filter_by(user_id=user_id).count()
        })

        print(f'📋 Clipboard synced: {len(content)} chars')

    except Exception as e:
        print(f'❌ Error: {e}')
        emit('error', {'message': str(e)})

@socketio.on('save_session')
def handle_save_session(data):
    try:
        user_id = data.get('user_id')
        session_name = data.get('name')
        tabs_data = data.get('tabs', [])

        session = Session(
            user_id=user_id,
            name=session_name,
            tabs=tabs_data,
            tab_count=len(tabs_data),
            size_mb=len(json.dumps(tabs_data).encode()) / (1024 * 1024)
        )
        db.session.add(session)
        db.session.commit()

        emit('session_saved', {'session': session.to_dict()})
        print(f'💾 Session saved: {session_name}')

    except Exception as e:
        print(f'❌ Error: {e}')
        emit('error', {'message': str(e)})

@socketio.on('productivity_update')
def handle_productivity_update(data):
    try:
        user_id = data.get('user_id')

        prod_log = ProductivityLog(
            user_id=user_id,
            focus_score=data.get('focus_score', 50),
            time_on_task=data.get('time_on_task', 0),
            distractions=data.get('distractions', 0),
            pomodoro_completed=data.get('pomodoro_completed', 0)
        )
        db.session.add(prod_log)
        db.session.commit()

        emit('productivity_recorded', {'log': prod_log.to_dict()})

    except Exception as e:
        print(f'❌ Error: {e}')
        emit('error', {'message': str(e)})

# ==================== REST API ENDPOINTS ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'version': '3.0'}), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not all([username, email, password]):
            return jsonify({'error': 'Missing fields'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username exists'}), 400

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return jsonify({'success': True, 'user_id': user.id}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401

        if jwt:
            token = jwt.encode(
                {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(days=30)},
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        else:
            token = user.id

        return jsonify({'success': True, 'token': token, 'user_id': user.id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    try:
        user_id = request.args.get('user_id')
        sessions = Session.query.filter_by(user_id=user_id).all()
        return jsonify([s.to_dict() for s in sessions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        session = Session(
            user_id=user_id,
            name=data.get('name', 'New Session'),
            tabs=data.get('tabs', []),
            tab_count=len(data.get('tabs', [])),
            size_mb=len(json.dumps(data.get('tabs', [])).encode()) / (1024 * 1024)
        )
        db.session.add(session)
        db.session.commit()

        return jsonify(session.to_dict()), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        db.session.delete(session)
        db.session.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clipboard', methods=['GET'])
def get_clipboard():
    try:
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 20, type=int)
        items = ClipboardItem.query.filter_by(user_id=user_id).order_by(
            ClipboardItem.created_at.desc()
        ).limit(limit).all()

        return jsonify([item.to_dict() for item in items]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clipboard', methods=['POST'])
def add_clipboard():
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        item = ClipboardItem(
            user_id=user_id,
            content=data.get('content'),
            content_type=data.get('content_type', 'text'),
            size_kb=len(data.get('content', '').encode()) / 1024
        )
        db.session.add(item)
        db.session.commit()

        return jsonify(item.to_dict()), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clipboard/<item_id>', methods=['DELETE'])
def delete_clipboard(item_id):
    try:
        item = ClipboardItem.query.get(item_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        db.session.delete(item)
        db.session.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/commands', methods=['GET'])
def get_commands():
    try:
        user_id = request.args.get('user_id')
        limit = request.args.get('limit', 50, type=int)
        commands = CommandLog.query.filter_by(user_id=user_id).order_by(
            CommandLog.created_at.desc()
        ).limit(limit).all()

        return jsonify([cmd.to_dict() for cmd in commands]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/productivity', methods=['GET'])
def get_productivity():
    try:
        user_id = request.args.get('user_id')
        days = request.args.get('days', 7, type=int)

        since = datetime.utcnow() - timedelta(days=days)
        logs = ProductivityLog.query.filter(
            ProductivityLog.user_id == user_id,
            ProductivityLog.created_at >= since
        ).all()

        return jsonify([log.to_dict() for log in logs]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/productivity/stats', methods=['GET'])
def get_productivity_stats():
    try:
        user_id = request.args.get('user_id')

        today = datetime.utcnow().date()
        today_logs = ProductivityLog.query.filter(
            ProductivityLog.user_id == user_id,
            db.func.date(ProductivityLog.created_at) == today
        ).all()

        avg_focus = sum(log.focus_score for log in today_logs) / len(today_logs) if today_logs else 0
        total_time = sum(log.time_on_task for log in today_logs) if today_logs else 0
        total_distractions = sum(log.distractions for log in today_logs) if today_logs else 0

        return jsonify({
            'avg_focus_score': int(avg_focus),
            'total_focus_time': total_time,
            'total_distractions': total_distractions,
            'pomodoros_completed': sum(log.pomodoro_completed for log in today_logs)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    try:
        user_id = request.args.get('user_id')

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        export_data = {
            'user': {'username': user.username, 'email': user.email},
            'sessions': [s.to_dict() for s in user.sessions],
            'clipboard': [c.to_dict() for c in user.clipboard_items],
            'commands': [cmd.to_dict() for cmd in user.commands],
            'exported_at': datetime.utcnow().isoformat()
        }

        filename = f'neura-sync-{user_id}.json'
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        return send_file(filename, as_attachment=True, download_name=filename), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        user_id = request.args.get('user_id')

        return jsonify({
            'total_sessions': Session.query.filter_by(user_id=user_id).count(),
            'total_clipboard': ClipboardItem.query.filter_by(user_id=user_id).count(),
            'total_commands': CommandLog.query.filter_by(user_id=user_id).count(),
            'connected_clients': len(connected_clients)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Neura Sync v3.0 Backend starting on port {port}...')
    socketio.run(app, host='0.0.0.0', port=port, debug=False)