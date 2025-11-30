import csv
import os
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

CSV_FILE = 'data/users.csv'

def ensure_csv_exists():
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'email', 'password_hash', 'first_name', 'last_name'])

ensure_csv_exists()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def get_user_from_csv(email):
    ensure_csv_exists()
    with open(CSV_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['email'] == email:
                return row
    return None

def add_user_to_csv(user_id, email, password_hash, first_name, last_name):
    ensure_csv_exists()
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([user_id, email, password_hash, first_name, last_name])

def email_exists_in_csv(email):
    return get_user_from_csv(email) is not None

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
        
        csv_user = get_user_from_csv(email)
        if csv_user and check_password_hash(csv_user['password_hash'], password):
            user = User.query.get(csv_user['id'])
            if user:
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
        
        if email_exists_in_csv(email):
            flash('An account with this email already exists.', 'error')
            return render_template('auth.html', mode='signup')
        
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        add_user_to_csv(user_id, email, password_hash, first_name, last_name)
        
        user = User()
        user.id = user_id
        user.email = email
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
