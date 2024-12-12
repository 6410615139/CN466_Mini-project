# routes/auth.py

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from utils.mongodb import mongo_user_create
from forms import LoginForm, RegisterForm

# Configure logging
logging.basicConfig(
    filename='logs/auth_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.get_user_by_username(username)
        hashed_password = user.password

        if user and check_password_hash(hashed_password, password):
            login_user(user)
            logger.info(f"User '{username}' logged in successfully.")
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home.index'))
        else:
            flash('Invalid username or password', 'danger')
            logger.warning(f"Failed login attempt for username: '{username}'")
    return render_template('login.html', form=form)

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Check if the username already exists
        if User.get_user_by_username(username):
            flash('Username already exists. Please choose a different one.', 'danger')
            logger.warning(f"Registration attempt failed - username '{username}' already exists.")
            return redirect(url_for('auth.register'))

        # Hash password and create the user
        user_data = {
            'password': generate_password_hash(password, method='pbkdf2:sha256'),
            'username': username,
            'pic': "",
            'is_admin': False,
            'limit': 0,
            'line': ""
        }
        user = User(user_data)
        user.create_user()
        logger.info(f"User '{username}' registered successfully.")
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    logger.info("User logged out.")
    return redirect(url_for('auth.login'))

# Line bot webhook endpoint
@auth_blueprint.route('/callback', methods=['POST'])
def line_callback():
    body = request.get_json()

    # Get the sender's line_id from the event
    for event in body['events']:
        line_id = event['source']['userId']  # This is the line_id

        # Check if the user is already registered
        user = User.get_user_by_line_id(line_id)
        if user:
            # User is already registered
            return jsonify({"status": "ok"})

        # Fetch user profile (display_name and picture_url)
        headers = {
            'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
        }
        profile_response = requests.get(LINE_PROFILE_URL + f"/{line_id}", headers=headers)
        profile_data = profile_response.json()

        display_name = profile_data['displayName']
        picture_url = profile_data['pictureUrl']

        # Hash password and create the user
        userdata = {
            'line': line_id,
            'username': display_name,
            'is_admin': False,
            'limit': 0,
        }

        # Register the user
        user = User(userdata)
        user.create_user()

        # Log the user in using Flask-Login (you might want to redirect or store session)
        login_user(user)

        # Respond to confirm the user is registered
        return jsonify({"status": "ok", "message": "User registered successfully"})

    return jsonify({"status": "error", "message": "No events found"})
