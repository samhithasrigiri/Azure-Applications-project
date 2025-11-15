"""
The flask application package.
"""
import logging
import os # Included for robustness, though not strictly used in basicConfig
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session

# --- Logging Implementation ---
# Configure basic logging to a file or standard output
logging.basicConfig(
    level=logging.INFO, # Set the minimum level to log
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
    datefmt='%Y-%m-%d %H:%M:%S',
)
# Get the Flask logger instance and export it for use in views.py
logger = logging.getLogger(__name__) 
# --- End Logging Implementation ---

app = Flask(__name__)
app.config.from_object(Config)
# TODO: Add any logging levels and handlers with app.logger
# The logging setup above addresses this initial configuration.
Session(app)
db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

import FlaskWebProject.views
