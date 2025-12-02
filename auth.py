import uuid
import secrets
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, current_user

from app import app, db
from models import User

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf_token():
    token = session.get('_csrf_token')
    form_token = request.form.get('csrf_token')
    if not token or token != form_token:
        return False
    return True

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if not validate_csrf_token():
            flash('Invalid request. Please try again.', 'error')
            return render_template('auth.html', mode='login')
        
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('auth.html', mode='login')
        
        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and check_password_hash(user.password_hash, password):
            login_user(user)
            next_url = session.pop('next_url', None)
            return redirect(next_url or url_for('index'))
        
        flash('Invalid email or password.', 'error')
        return render_template('auth.html', mode='login')
    
    return render_template('auth.html', mode='login')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if not validate_csrf_token():
            flash('Invalid request. Please try again.', 'error')
            return render_template('auth.html', mode='signup')
        
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('auth.html', mode='signup')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth.html', mode='signup')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth.html', mode='signup')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('auth.html', mode='signup')
        
        user_id = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)
        
        user = User()
        user.id = user_id
        user.email = email
        user.password_hash = hashed_password
        user.first_name = first_name if first_name else None
        user.last_name = last_name if last_name else None
        user.profile_image_url = None
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth.html', mode='signup')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@auth_bp.route('/error')
def error():
    return render_template('403.html'), 403

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session["next_url"] = request.url
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
