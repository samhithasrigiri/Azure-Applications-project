"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, flash, redirect, request, session, url_for
from werkzeug.urls import url_parse
from config import Config
# Updated import to include the logger instance from __init__.py
from FlaskWebProject import app, db, logger 
from FlaskWebProject.forms import LoginForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required
from FlaskWebProject.models import User, Post
import msal
import uuid
import json # Used for token cache serialization/deserialization

imageSourceUrl = 'https://'+ app.config['BLOB_ACCOUNT'] + '.blob.core.windows.net/' + app.config['BLOB_CONTAINER'] + '/'

# --- MSAL Helper Functions (B. Microsoft Authentication) ---

def _load_cache():
    """Loads the MSAL token cache from the Flask session."""
    cache = msal.TokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    """Saves the MSAL token cache to the Flask session if it has changed."""
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None, authority=None):
    """Initializes and returns the msal.ConfidentialClientApplication object."""
    # Retrieve settings from config
    CLIENT_ID = app.config['CLIENT_ID']
    CLIENT_SECRET = app.config['CLIENT_SECRET']
    
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=authority or app.config['AUTHORITY'],
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )

def _build_auth_url(authority=None, scopes=None, state=None):
    """Builds and returns the MSAL authorization request URL."""
    msal_app = _build_msal_app(authority=authority)
    return msal_app.get_authorization_request_url(
        scopes or Config.SCOPE,
        state=state,
        # Redirect URI must match the one registered in Entra ID
        redirect_uri=url_for("authorized", _external=True)
    )
# --- End MSAL Helper Functions ---


@app.route('/')
@app.route('/home')
@login_required
def home():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    posts = Post.query.all()
    return render_template(
        'index.html',
        title='Home Page',
        posts=posts
    )

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm(request.form)
    if form.validate_on_submit():
        post = Post()
        post.save_changes(form, request.files['image_path'], current_user.id, new=True)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Create Post',
        imageSource=imageSourceUrl,
        form=form
    )


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    post = Post.query.get(int(id))
    form = PostForm(formdata=request.form, obj=post)
    if form.validate_on_submit():
        post.save_changes(form, request.files['image_path'], current_user.id)
        return redirect(url_for('home'))
    return render_template(
        'post.html',
        title='Edit Post',
        imageSource=imageSourceUrl,
        form=form
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    
    # Standard local login attempt
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            # A. Logging Implementation: Unsuccessful Login
            logger.warning(f"Invalid login attempt for username: {form.username.data}")
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        # A. Logging Implementation: Successful Login
        logger.info(f"User {user.username} logged in successfully using local credentials.")
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('home')
        return redirect(next_page)
    
    # MSAL Integration: Build the sign-in URL for the login template
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=Config.SCOPE, state=session["state"])
    return render_template('login.html', title='Sign In', form=form, auth_url=auth_url)

@app.route(Config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    # State check to mitigate CSRF
    if request.args.get('state') != session.get("state"):
        logger.warning("MSAL authorized endpoint: State mismatch detected. Possible CSRF attempt.")
        return redirect(url_for("home"))
    
    # Handle authentication/authorization failure from AAD
    if "error" in request.args:
        # A. Logging Implementation: MSAL Error
        logger.error(f"MSAL authorization failed. Error: {request.args.get('error_description', 'Unknown error')}")
        return render_template("auth_error.html", result=request.args)
    
    if request.args.get('code'):
        cache = _load_cache()
        msal_app = _build_msal_app(cache=cache)
        
        # B. Microsoft Authentication (MSAL): Acquire Token
        result = msal_app.acquire_token_by_authorization_code(
            request.args['code'],
            scopes=Config.SCOPE,
            redirect_uri=url_for("authorized", _external=True)
        )
        
        if "error" in result:
            # A. Logging Implementation: Token acquisition failure
            logger.error(f"MSAL token acquisition failed. Error: {result.get('error_description', 'Unknown error')}")
            return render_template("auth_error.html", result=result)
        
        # Successful MSAL login
        session["user"] = result.get("id_token_claims")
        
        # Map MSAL authenticated user to CMS 'admin' account
        user = User.query.filter_by(username="admin").first()
        login_user(user)
        _save_cache(cache)
        
        # A. Logging Implementation: Successful MSAL login
        msal_user_id = session['user'].get('preferred_username', session['user'].get('name', 'UNKNOWN_MSAL_USER'))
        logger.info(f"MSAL user '{msal_user_id}' logged in successfully and mapped to '{user.username}' CMS user")
        
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    # A. Logging Implementation: Log user logout
    if current_user.is_authenticated:
        logger.info(f"User {current_user.username} logged out.")
        
    logout_user()
    
    if session.get("user"): # Checks if the user logged in via MSAL
        # Wipe out user and its token cache from session
        session.clear()
        # Redirect to AAD logout endpoint
        return redirect(
            Config.AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for("login", _external=True))

    return redirect(url_for('login'))
