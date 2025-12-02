from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import os
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)

# Session secret - generate a fallback for development
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Proxy fix for running behind reverse proxies (Render, etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration - handle Render's postgres:// vs postgresql:// difference
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Please configure a PostgreSQL database on Render: "
        "1. Go to Render Dashboard > New > PostgreSQL "
        "2. Create a free database "
        "3. Copy the 'Internal Database URL' "
        "4. Add it as DATABASE_URL in your web service's Environment settings"
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db.init_app(app)
