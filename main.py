import os
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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
    
    profiles = db.relationship('Profile', backref='user', cascade='all, delete-orphan')
    devices = db.relationship('Device', backref='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Profile(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    profile_type = db.Column(db.String(20), default='personal')  # work, study, personal, entertainment
    icon = db.Column(db.String(10), default='👤')
    preferences = db.Column(db.JSON, default=dict)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    tabs = db.relationship('TabState', backref='profile', cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='profile', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'profile_type': self.profile_type,
            'icon': self.icon, 'is_active': self.is_active,
            'tab_count': len(self.tabs), 'bookmark_count': len(self.bookmarks)
        }

class Device(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    device_name = db.Column(db.String(100))
    device_type = db.Column(db.String(20))  # desktop, mobile, tablet
    browser = db.Column(db.String(50))
    os = db.Column(db.String(50))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)
    trust_level = db.Column(db.Integer, default=1)  # 1=new, 2=trusted, 3=verified
    socket_id = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id, 'device_name': self.device_name, 'device_type': self.device_type,
            'browser': self.browser, 'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }

class TabState(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = db.Column(db.String(36), db.ForeignKey('profile.id'), nullable=False)
    device_id = db.Column(db.String(36), db.ForeignKey('device.id'))
    url = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(500))
    favicon = db.Column(db.Text)
    position = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_frozen = db.Column(db.Boolean, default=False)
    is_sleeping = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.String(36))
    group_name = db.Column(db.String(100))
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id, 'url': self.url, 'title': self.title, 'favicon': self.favicon,
            'position': self.position, 'is_pinned': self.is_pinned, 'is_frozen': self.is_frozen,
            'group_name': self.group_name, 'last_accessed': self.last_accessed.isoformat()
        }

class TabGroup(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = db.Column(db.String(36), db.ForeignKey('profile.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), default='#6366f1')
    icon = db.Column(db.String(10))
    is_collapsed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Session(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    profile_id = db.Column(db.String(36))
    name = db.Column(db.String(255), nullable=False)
    tabs = db.Column(db.JSON, default=list)
    tab_count = db.Column(db.Integer, default=0)
    size_mb = db.Column(db.Float, default=0.0)
    is_auto_saved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'tabs': self.tabs, 'tab_count': self.tab_count,
            'size_mb': self.size_mb, 'created_at': self.created_at.isoformat(), 'is_auto_saved': self.is_auto_saved
        }

class Bookmark(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = db.Column(db.String(36), db.ForeignKey('profile.id'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    favicon = db.Column(db.Text)
    folder_id = db.Column(db.String(36))
    folder_name = db.Column(db.String(200))
    tags = db.Column(db.JSON, default=list)
    ai_category = db.Column(db.String(100))
    ai_metadata = db.Column(db.JSON, default=dict)
    is_favorite = db.Column(db.Boolean, default=False)
    is_dead = db.Column(db.Boolean, default=False)
    visit_count = db.Column(db.Integer, default=0)
    last_visited = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id, 'url': self.url, 'title': self.title, 'description': self.description,
            'folder_name': self.folder_name, 'tags': self.tags, 'ai_category': self.ai_category,
            'is_favorite': self.is_favorite, 'visit_count': self.visit_count, 'created_at': self.created_at.isoformat()
        }

class BookmarkFolder(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = db.Column(db.String(36), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(10))
    parent_id = db.Column(db.String(36))
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HistoryEntry(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    profile_id = db.Column(db.String(36))
    url = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(500))
    favicon = db.Column(db.Text)
    category = db.Column(db.String(100))
    topic = db.Column(db.String(100))
    visit_count = db.Column(db.Integer, default=1)
    duration_seconds = db.Column(db.Integer, default=0)
    thumbnail = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    visited_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id, 'url': self.url, 'title': self.title, 'category': self.category,
            'visit_count': self.visit_count, 'duration_seconds': self.duration_seconds,
            'visited_at': self.visited_at.isoformat()
        }

class ReadingItem(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    url = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    image = db.Column(db.Text)
    content = db.Column(db.Text)  # Cleaned article content
    reading_time = db.Column(db.Integer, default=0)  # minutes
    progress = db.Column(db.Float, default=0.0)  # 0-100
    highlights = db.Column(db.JSON, default=list)
    notes = db.Column(db.JSON, default=list)
    is_read = db.Column(db.Boolean, default=False)
    is_favorite = db.Column(db.Boolean, default=False)
    is_offline = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id, 'url': self.url, 'title': self.title, 'description': self.description,
            'reading_time': self.reading_time, 'progress': self.progress, 'is_read': self.is_read,
            'is_favorite': self.is_favorite, 'is_offline': self.is_offline, 'created_at': self.created_at.isoformat()
        }

class ClipboardItem(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(50), default='text')  # text, image, code, link
    size_kb = db.Column(db.Float, default=0.0)
    source_device = db.Column(db.String(100))
    extra_data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id, 'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'full_content': self.content, 'content_type': self.content_type,
            'size_kb': self.size_kb, 'created_at': self.created_at.isoformat()
        }

class CommandLog(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    command = db.Column(db.String(500), nullable=False)
    command_type = db.Column(db.String(50))
    device_count = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='sent')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PrivacyEvent(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    event_type = db.Column(db.String(50))  # breach_alert, tracker_blocked, fingerprint_blocked
    severity = db.Column(db.String(20), default='info')  # info, warning, critical
    domain = db.Column(db.String(500))
    details = db.Column(db.JSON, default=dict)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id, 'event_type': self.event_type, 'severity': self.severity,
            'domain': self.domain, 'details': self.details, 'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat()
        }

class AnalyticsSnapshot(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    profile_id = db.Column(db.String(36))
    date = db.Column(db.Date, default=lambda: datetime.utcnow().date())
    sites_visited = db.Column(db.Integer, default=0)
    browsing_time_minutes = db.Column(db.Integer, default=0)
    productivity_score = db.Column(db.Integer, default=50)
    focus_time_minutes = db.Column(db.Integer, default=0)
    pomodoros_completed = db.Column(db.Integer, default=0)
    distractions_blocked = db.Column(db.Integer, default=0)
    top_categories = db.Column(db.JSON, default=list)
    hourly_breakdown = db.Column(db.JSON, default=dict)
    
    def to_dict(self):
        return {
            'id': self.id, 'date': str(self.date), 'sites_visited': self.sites_visited,
            'browsing_time_minutes': self.browsing_time_minutes, 'productivity_score': self.productivity_score,
            'focus_time_minutes': self.focus_time_minutes, 'pomodoros_completed': self.pomodoros_completed,
            'top_categories': self.top_categories
        }

class FocusSession(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    duration_minutes = db.Column(db.Integer, default=25)
    actual_duration = db.Column(db.Integer, default=0)
    blocked_sites = db.Column(db.JSON, default=list)
    distractions_attempted = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

class BlockedSite(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    domain = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(50))  # social, entertainment, news
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Credential(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    site_url = db.Column(db.String(500), nullable=False)
    site_name = db.Column(db.String(200))
    username = db.Column(db.String(200))
    encrypted_password = db.Column(db.Text)  # Encrypted with user's master key
    notes = db.Column(db.Text)
    category = db.Column(db.String(50))  # banking, social, work, etc.
    is_favorite = db.Column(db.Boolean, default=False)
    last_used = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id, 'site_url': self.site_url, 'site_name': self.site_name,
            'username': self.username, 'category': self.category, 'is_favorite': self.is_favorite,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat()
        }

class Extension(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    profile_id = db.Column(db.String(36))
    extension_id = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(200))
    version = db.Column(db.String(50))
    browser = db.Column(db.String(50))
    is_enabled = db.Column(db.Boolean, default=True)
    settings = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id, 'extension_id': self.extension_id, 'name': self.name,
            'version': self.version, 'browser': self.browser, 'is_enabled': self.is_enabled
        }

# ==================== WEBSOCKET EVENTS ====================

connected_clients = {}
user_devices = {}

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    connected_clients[client_id] = {'connected_at': datetime.utcnow(), 'user_id': None}
    print(f'✓ Client connected: {client_id} | Total: {len(connected_clients)}')
    emit('connection_response', {'message': 'Connected', 'client_id': client_id})

@socketio.on('register_device')
def handle_register_device(data):
    client_id = request.sid
    user_id = data.get('user_id', 'guest')
    
    connected_clients[client_id]['user_id'] = user_id
    join_room(user_id)
    
    if user_id not in user_devices:
        user_devices[user_id] = set()
    user_devices[user_id].add(client_id)
    
    device_count = len(user_devices.get(user_id, set()))
    print(f'📱 Device registered: {client_id[:8]} for user {user_id} | Devices: {device_count}')
    
    emit('device_registered', {'user_id': user_id, 'device_count': device_count, 'client_id': client_id})
    socketio.emit('device_count', {'count': device_count}, room=user_id)

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    user_id = connected_clients.get(client_id, {}).get('user_id')
    
    if client_id in connected_clients:
        del connected_clients[client_id]
    
    if user_id and user_id in user_devices:
        user_devices[user_id].discard(client_id)
        if not user_devices[user_id]:
            del user_devices[user_id]
        else:
            socketio.emit('device_count', {'count': len(user_devices[user_id])}, room=user_id)
    
    print(f'✗ Client disconnected: {client_id} | Total: {len(connected_clients)}')

@socketio.on('send_command')
def handle_command(data):
    try:
        command = data.get('command', '').strip()
        user_id = data.get('user_id', 'anonymous')
        sender_id = request.sid

        if not command:
            emit('error', {'message': 'Empty command'})
            return

        cmd_type = 'open' if command.startswith('open') else 'search' if command.startswith('search') else 'custom'

        try:
            cmd_log = CommandLog(user_id=user_id, command=command, command_type=cmd_type,
                                device_count=len(user_devices.get(user_id, set())), status='executing')
            db.session.add(cmd_log)
            db.session.commit()
        except:
            pass

        device_count = len(user_devices.get(user_id, set()))
        payload = {'command': command, 'cmd_type': cmd_type, 'timestamp': datetime.utcnow().isoformat(),
                   'sender': sender_id[:8], 'device_count': device_count}

        print(f'📤 Broadcasting command: {command} to {user_id} ({device_count} devices)')
        
        if user_id in user_devices:
            socketio.emit('command_received', payload, room=user_id)
        
        emit('command_ack', {'status': 'success', 'message': f'Command sent to {device_count} device(s)'})

    except Exception as e:
        print(f'❌ Command Error: {e}')
        emit('error', {'message': str(e)})

@socketio.on('sync_clipboard')
def handle_clipboard_sync(data):
    try:
        user_id = data.get('user_id')
        content = data.get('content')

        if not content:
            return

        item = ClipboardItem(user_id=user_id, content=content, content_type=data.get('content_type', 'text'),
                            size_kb=len(content.encode()) / 1024)
        db.session.add(item)
        db.session.commit()

        socketio.emit('clipboard_updated', {'item': item.to_dict()}, room=user_id)
        print(f'📋 Clipboard synced: {len(content)} chars')

    except Exception as e:
        print(f'❌ Clipboard Error: {e}')

@socketio.on('sync_tabs')
def handle_tab_sync(data):
    try:
        user_id = data.get('user_id')
        profile_id = data.get('profile_id')
        tabs = data.get('tabs', [])

        socketio.emit('tabs_updated', {'tabs': tabs, 'profile_id': profile_id}, room=user_id)
        print(f'🗂️ Tabs synced: {len(tabs)} tabs')

    except Exception as e:
        print(f'❌ Tab Sync Error: {e}')

@socketio.on('sync_bookmarks')
def handle_bookmark_sync(data):
    try:
        user_id = data.get('user_id')
        socketio.emit('bookmarks_updated', data, room=user_id)
        print(f'⭐ Bookmarks synced')
    except Exception as e:
        print(f'❌ Bookmark Sync Error: {e}')

@socketio.on('save_session')
def handle_save_session(data):
    try:
        user_id = data.get('user_id')
        session = Session(user_id=user_id, name=data.get('name'), tabs=data.get('tabs', []),
                         tab_count=len(data.get('tabs', [])))
        db.session.add(session)
        db.session.commit()
        emit('session_saved', {'session': session.to_dict()})
        print(f'💾 Session saved: {session.name}')
    except Exception as e:
        print(f'❌ Session Error: {e}')

@socketio.on('focus_start')
def handle_focus_start(data):
    try:
        user_id = data.get('user_id')
        focus = FocusSession(user_id=user_id, duration_minutes=data.get('duration', 25))
        db.session.add(focus)
        db.session.commit()
        socketio.emit('focus_started', {'session_id': focus.id}, room=user_id)
    except Exception as e:
        print(f'❌ Focus Error: {e}')

@socketio.on('focus_complete')
def handle_focus_complete(data):
    try:
        session_id = data.get('session_id')
        focus = FocusSession.query.get(session_id)
        if focus:
            focus.completed = True
            focus.ended_at = datetime.utcnow()
            focus.actual_duration = data.get('actual_duration', 0)
            db.session.commit()
    except Exception as e:
        print(f'❌ Focus Complete Error: {e}')

# ==================== REST API ENDPOINTS ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'version': '4.0', 'features': 75}), 200

# Profile Management
@app.route('/api/v1/profiles', methods=['GET', 'POST'])
def profiles():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        profiles = Profile.query.filter_by(user_id=user_id).all() if user_id else []
        return jsonify([p.to_dict() for p in profiles])
    
    data = request.get_json()
    profile = Profile(user_id=data.get('user_id'), name=data.get('name'),
                     profile_type=data.get('type', 'personal'), icon=data.get('icon', '👤'))
    db.session.add(profile)
    db.session.commit()
    return jsonify(profile.to_dict()), 201

@app.route('/api/v1/profiles/<profile_id>', methods=['PUT', 'DELETE'])
def profile_detail(profile_id):
    profile = Profile.query.get_or_404(profile_id)
    if request.method == 'DELETE':
        db.session.delete(profile)
        db.session.commit()
        return jsonify({'success': True})
    
    data = request.get_json()
    if 'name' in data: profile.name = data['name']
    if 'is_active' in data: profile.is_active = data['is_active']
    db.session.commit()
    return jsonify(profile.to_dict())

# Device Management
@app.route('/api/v1/devices', methods=['GET', 'POST'])
def devices():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    if request.method == 'GET':
        devices = Device.query.filter_by(user_id=user_id).all() if user_id else []
        return jsonify([d.to_dict() for d in devices])
    
    data = request.get_json()
    device = Device(user_id=data.get('user_id'), device_name=data.get('name'),
                   device_type=data.get('type'), browser=data.get('browser'))
    db.session.add(device)
    db.session.commit()
    return jsonify(device.to_dict()), 201

# Tab Management
@app.route('/api/v1/tabs', methods=['GET', 'POST'])
def tabs():
    profile_id = request.args.get('profile_id') or (request.get_json() or {}).get('profile_id')
    if request.method == 'GET':
        tabs = TabState.query.filter_by(profile_id=profile_id).order_by(TabState.position).all()
        return jsonify([t.to_dict() for t in tabs])
    
    data = request.get_json()
    tab = TabState(profile_id=profile_id, url=data.get('url'), title=data.get('title'),
                  favicon=data.get('favicon'), position=data.get('position', 0))
    db.session.add(tab)
    db.session.commit()
    return jsonify(tab.to_dict()), 201

@app.route('/api/v1/tabs/bulk', methods=['POST'])
def bulk_tabs():
    data = request.get_json()
    profile_id = data.get('profile_id')
    tabs_data = data.get('tabs', [])
    
    TabState.query.filter_by(profile_id=profile_id).delete()
    
    for idx, tab in enumerate(tabs_data):
        t = TabState(profile_id=profile_id, url=tab.get('url'), title=tab.get('title'),
                    favicon=tab.get('favicon'), position=idx)
        db.session.add(t)
    
    db.session.commit()
    return jsonify({'success': True, 'count': len(tabs_data)})

# Session Management
@app.route('/api/v1/sessions', methods=['GET', 'POST'])
def sessions():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    if request.method == 'GET':
        sessions = Session.query.filter_by(user_id=user_id).order_by(Session.created_at.desc()).all()
        return jsonify([s.to_dict() for s in sessions])
    
    data = request.get_json()
    session = Session(user_id=user_id, name=data.get('name'), tabs=data.get('tabs', []),
                     tab_count=len(data.get('tabs', [])))
    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_dict()), 201

@app.route('/api/v1/sessions/<session_id>', methods=['GET', 'DELETE'])
def session_detail(session_id):
    session = Session.query.get_or_404(session_id)
    if request.method == 'DELETE':
        db.session.delete(session)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify(session.to_dict())

# Bookmark Management
@app.route('/api/v1/bookmarks', methods=['GET', 'POST'])
def bookmarks():
    profile_id = request.args.get('profile_id') or (request.get_json() or {}).get('profile_id')
    if request.method == 'GET':
        bookmarks = Bookmark.query.filter_by(profile_id=profile_id).order_by(Bookmark.created_at.desc()).all()
        return jsonify([b.to_dict() for b in bookmarks])
    
    data = request.get_json()
    bookmark = Bookmark(profile_id=profile_id, url=data.get('url'), title=data.get('title'),
                       description=data.get('description'), folder_name=data.get('folder'),
                       tags=data.get('tags', []))
    db.session.add(bookmark)
    db.session.commit()
    return jsonify(bookmark.to_dict()), 201

@app.route('/api/v1/bookmarks/<bookmark_id>', methods=['PUT', 'DELETE'])
def bookmark_detail(bookmark_id):
    bookmark = Bookmark.query.get_or_404(bookmark_id)
    if request.method == 'DELETE':
        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({'success': True})
    
    data = request.get_json()
    for key in ['title', 'description', 'folder_name', 'tags', 'is_favorite']:
        if key in data: setattr(bookmark, key, data[key])
    db.session.commit()
    return jsonify(bookmark.to_dict())

@app.route('/api/v1/bookmarks/duplicates', methods=['GET'])
def find_duplicates():
    profile_id = request.args.get('profile_id')
    from sqlalchemy import func
    dupes = db.session.query(Bookmark.url, func.count(Bookmark.id)).filter_by(profile_id=profile_id)\
        .group_by(Bookmark.url).having(func.count(Bookmark.id) > 1).all()
    return jsonify([{'url': d[0], 'count': d[1]} for d in dupes])

# History Management
@app.route('/api/v1/history', methods=['GET', 'POST'])
def history():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    if request.method == 'GET':
        limit = request.args.get('limit', 50, type=int)
        entries = HistoryEntry.query.filter_by(user_id=user_id).order_by(HistoryEntry.visited_at.desc()).limit(limit).all()
        return jsonify([e.to_dict() for e in entries])
    
    data = request.get_json()
    entry = HistoryEntry(user_id=user_id, url=data.get('url'), title=data.get('title'),
                        category=data.get('category'))
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.to_dict()), 201

@app.route('/api/v1/history/timeline', methods=['GET'])
def history_timeline():
    user_id = request.args.get('user_id')
    date = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    entries = HistoryEntry.query.filter(HistoryEntry.user_id == user_id,
        db.func.date(HistoryEntry.visited_at) == date).order_by(HistoryEntry.visited_at.desc()).all()
    
    timeline = {}
    for e in entries:
        hour = e.visited_at.strftime('%H:00')
        if hour not in timeline:
            timeline[hour] = []
        timeline[hour].append(e.to_dict())
    
    return jsonify({'date': date, 'timeline': timeline})

# Reading List
@app.route('/api/v1/reading-list', methods=['GET', 'POST'])
def reading_list():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    if request.method == 'GET':
        items = ReadingItem.query.filter_by(user_id=user_id).order_by(ReadingItem.created_at.desc()).all()
        return jsonify([i.to_dict() for i in items])
    
    data = request.get_json()
    item = ReadingItem(user_id=user_id, url=data.get('url'), title=data.get('title'),
                      description=data.get('description'), reading_time=data.get('reading_time', 5))
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

@app.route('/api/v1/reading-list/<item_id>', methods=['PUT', 'DELETE'])
def reading_item(item_id):
    item = ReadingItem.query.get_or_404(item_id)
    if request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    
    data = request.get_json()
    for key in ['is_read', 'is_favorite', 'progress', 'highlights', 'notes']:
        if key in data: setattr(item, key, data[key])
    db.session.commit()
    return jsonify(item.to_dict())

# Clipboard
@app.route('/api/v1/clipboard', methods=['GET', 'POST', 'DELETE'])
def clipboard():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    if request.method == 'GET':
        items = ClipboardItem.query.filter_by(user_id=user_id).order_by(ClipboardItem.created_at.desc()).limit(50).all()
        return jsonify([i.to_dict() for i in items])
    
    if request.method == 'DELETE':
        ClipboardItem.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({'success': True})
    
    data = request.get_json()
    item = ClipboardItem(user_id=user_id, content=data.get('content'),
                        content_type=data.get('content_type', 'text'),
                        size_kb=len(data.get('content', '').encode()) / 1024)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201

# Privacy Events
@app.route('/api/v1/privacy/events', methods=['GET', 'POST'])
def privacy_events():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    if request.method == 'GET':
        events = PrivacyEvent.query.filter_by(user_id=user_id).order_by(PrivacyEvent.created_at.desc()).limit(50).all()
        return jsonify([e.to_dict() for e in events])
    
    data = request.get_json()
    event = PrivacyEvent(user_id=user_id, event_type=data.get('event_type'),
                        severity=data.get('severity', 'info'), domain=data.get('domain'),
                        details=data.get('details', {}))
    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201

# Analytics
@app.route('/api/v1/analytics', methods=['GET'])
def analytics():
    user_id = request.args.get('user_id')
    days = request.args.get('days', 7, type=int)
    
    since = datetime.utcnow() - timedelta(days=days)
    snapshots = AnalyticsSnapshot.query.filter(AnalyticsSnapshot.user_id == user_id,
        AnalyticsSnapshot.date >= since.date()).order_by(AnalyticsSnapshot.date.desc()).all()
    
    return jsonify([s.to_dict() for s in snapshots])

@app.route('/api/v1/analytics/today', methods=['GET', 'POST'])
def analytics_today():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    today = datetime.utcnow().date()
    
    snapshot = AnalyticsSnapshot.query.filter_by(user_id=user_id, date=today).first()
    
    if request.method == 'GET':
        if not snapshot:
            snapshot = AnalyticsSnapshot(user_id=user_id, date=today)
            db.session.add(snapshot)
            db.session.commit()
        return jsonify(snapshot.to_dict())
    
    data = request.get_json()
    if not snapshot:
        snapshot = AnalyticsSnapshot(user_id=user_id, date=today)
        db.session.add(snapshot)
    
    for key in ['sites_visited', 'browsing_time_minutes', 'productivity_score', 
                'focus_time_minutes', 'pomodoros_completed', 'distractions_blocked']:
        if key in data: setattr(snapshot, key, data[key])
    
    db.session.commit()
    return jsonify(snapshot.to_dict())

# Focus Mode
@app.route('/api/v1/focus/blocked-sites', methods=['GET', 'POST', 'DELETE'])
def blocked_sites():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    
    if request.method == 'GET':
        sites = BlockedSite.query.filter_by(user_id=user_id, is_active=True).all()
        return jsonify([{'id': s.id, 'domain': s.domain, 'category': s.category} for s in sites])
    
    if request.method == 'DELETE':
        site_id = request.args.get('site_id')
        if site_id:
            BlockedSite.query.filter_by(id=site_id).delete()
            db.session.commit()
        return jsonify({'success': True})
    
    data = request.get_json()
    site = BlockedSite(user_id=user_id, domain=data.get('domain'), category=data.get('category'))
    db.session.add(site)
    db.session.commit()
    return jsonify({'id': site.id, 'domain': site.domain}), 201

# AI Search (Placeholder)
@app.route('/api/v1/search', methods=['POST'])
def ai_search():
    data = request.get_json()
    query = data.get('query', '').lower()
    user_id = data.get('user_id')
    
    results = []
    
    # Search bookmarks
    bookmarks = Bookmark.query.filter(Bookmark.title.ilike(f'%{query}%')).limit(10).all()
    for b in bookmarks:
        results.append({'type': 'bookmark', 'title': b.title, 'url': b.url, 'score': 0.9})
    
    # Search history
    history = HistoryEntry.query.filter(HistoryEntry.title.ilike(f'%{query}%')).limit(10).all()
    for h in history:
        results.append({'type': 'history', 'title': h.title, 'url': h.url, 'score': 0.8})
    
    # Search reading list
    reading = ReadingItem.query.filter(ReadingItem.title.ilike(f'%{query}%')).limit(10).all()
    for r in reading:
        results.append({'type': 'reading', 'title': r.title, 'url': r.url, 'score': 0.85})
    
    # Search clipboard
    clipboard = ClipboardItem.query.filter(ClipboardItem.content.ilike(f'%{query}%')).limit(5).all()
    for c in clipboard:
        results.append({'type': 'clipboard', 'content': c.content[:100], 'score': 0.7})
    
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return jsonify({'query': query, 'results': results[:20]})

# Credential Vault
@app.route('/api/v1/vault', methods=['GET', 'POST'])
def vault():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    
    if request.method == 'GET':
        credentials = Credential.query.filter_by(user_id=user_id).order_by(Credential.site_name).all()
        return jsonify([c.to_dict() for c in credentials])
    
    data = request.get_json()
    credential = Credential(
        user_id=user_id,
        site_url=data.get('site_url'),
        site_name=data.get('site_name'),
        username=data.get('username'),
        encrypted_password=data.get('encrypted_password'),
        notes=data.get('notes'),
        category=data.get('category')
    )
    db.session.add(credential)
    db.session.commit()
    return jsonify(credential.to_dict()), 201

@app.route('/api/v1/vault/<credential_id>', methods=['GET', 'PUT', 'DELETE'])
def vault_detail(credential_id):
    credential = Credential.query.get_or_404(credential_id)
    
    if request.method == 'DELETE':
        db.session.delete(credential)
        db.session.commit()
        return jsonify({'success': True})
    
    if request.method == 'PUT':
        data = request.get_json()
        for key in ['site_url', 'site_name', 'username', 'encrypted_password', 'notes', 'category', 'is_favorite']:
            if key in data: setattr(credential, key, data[key])
        db.session.commit()
    
    return jsonify(credential.to_dict())

# Extension Management
@app.route('/api/v1/extensions', methods=['GET', 'POST'])
def extensions():
    user_id = request.args.get('user_id') or (request.get_json() or {}).get('user_id')
    profile_id = request.args.get('profile_id')
    
    if request.method == 'GET':
        query = Extension.query.filter_by(user_id=user_id)
        if profile_id:
            query = query.filter_by(profile_id=profile_id)
        exts = query.all()
        return jsonify([e.to_dict() for e in exts])
    
    data = request.get_json()
    ext = Extension(
        user_id=user_id,
        profile_id=data.get('profile_id'),
        extension_id=data.get('extension_id'),
        name=data.get('name'),
        version=data.get('version'),
        browser=data.get('browser'),
        settings=data.get('settings', {})
    )
    db.session.add(ext)
    db.session.commit()
    return jsonify(ext.to_dict()), 201

@app.route('/api/v1/extensions/<ext_id>', methods=['PUT', 'DELETE'])
def extension_detail(ext_id):
    ext = Extension.query.get_or_404(ext_id)
    
    if request.method == 'DELETE':
        db.session.delete(ext)
        db.session.commit()
        return jsonify({'success': True})
    
    data = request.get_json()
    for key in ['is_enabled', 'settings']:
        if key in data: setattr(ext, key, data[key])
    db.session.commit()
    return jsonify(ext.to_dict())

# Tab Groups
@app.route('/api/v1/tab-groups', methods=['GET', 'POST'])
def tab_groups():
    profile_id = request.args.get('profile_id') or (request.get_json() or {}).get('profile_id')
    
    if request.method == 'GET':
        groups = TabGroup.query.filter_by(profile_id=profile_id).all()
        return jsonify([{'id': g.id, 'name': g.name, 'color': g.color, 'icon': g.icon} for g in groups])
    
    data = request.get_json()
    group = TabGroup(profile_id=profile_id, name=data.get('name'), color=data.get('color', '#6366f1'),
                    icon=data.get('icon'))
    db.session.add(group)
    db.session.commit()
    return jsonify({'id': group.id, 'name': group.name}), 201

# Bookmark Folders
@app.route('/api/v1/bookmark-folders', methods=['GET', 'POST'])
def bookmark_folders():
    profile_id = request.args.get('profile_id') or (request.get_json() or {}).get('profile_id')
    
    if request.method == 'GET':
        folders = BookmarkFolder.query.filter_by(profile_id=profile_id).order_by(BookmarkFolder.position).all()
        return jsonify([{'id': f.id, 'name': f.name, 'icon': f.icon, 'parent_id': f.parent_id} for f in folders])
    
    data = request.get_json()
    folder = BookmarkFolder(profile_id=profile_id, name=data.get('name'), icon=data.get('icon'),
                           parent_id=data.get('parent_id'))
    db.session.add(folder)
    db.session.commit()
    return jsonify({'id': folder.id, 'name': folder.name}), 201

# Stats Summary
@app.route('/api/v1/stats', methods=['GET'])
def stats_summary():
    user_id = request.args.get('user_id')
    profile_id = request.args.get('profile_id')
    
    stats = {
        'devices': Device.query.filter_by(user_id=user_id).count() if user_id else 0,
        'tabs': TabState.query.filter_by(profile_id=profile_id).count() if profile_id else 0,
        'bookmarks': Bookmark.query.filter_by(profile_id=profile_id).count() if profile_id else 0,
        'clipboard': ClipboardItem.query.filter_by(user_id=user_id).count() if user_id else 0,
        'history': HistoryEntry.query.filter_by(user_id=user_id).count() if user_id else 0,
        'reading_list': ReadingItem.query.filter_by(user_id=user_id).count() if user_id else 0,
        'sessions': Session.query.filter_by(user_id=user_id).count() if user_id else 0,
        'credentials': Credential.query.filter_by(user_id=user_id).count() if user_id else 0
    }
    return jsonify(stats)

# ==================== APP STARTUP ====================

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print('🚀 NeuraSync v4.0 Backend starting on port 5000...')
    print('📦 Features: 75+ browser sync capabilities')
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
