import logging
import requests
import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from models import User
from utils.mongodb import mongo_user_create, mongo_user_find_line, mongo_user_find_uname
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(
    filename='logs/line_auth_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

line_auth_blueprint = Blueprint('line_auth', __name__)

# LINE Login credentials
LINE_CLIENT_ID = os.environ['LINE_CHANNEL_ID']
LINE_CLIENT_SECRET = os.environ['LINE_CHANNEL_SECRET']
LINE_REDIRECT_URI = os.environ['CALLBACK_URL']

@line_auth_blueprint.route('/login', methods=['GET'])
def login():
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state  # Store the state in the session

    line_auth_url = (
        f"https://access.line.me/oauth2/v2.1/authorize?response_type=code"
        f"&client_id={LINE_CLIENT_ID}"
        f"&redirect_uri={LINE_REDIRECT_URI}"
        f"&state={state}"  # Include the generated state
        f"&scope=profile%20openid%20email"
    )
    return redirect(line_auth_url)

@line_auth_blueprint.route('/callback', methods=['GET'])
def line_callback():
    # Get the state from the callback
    state = request.args.get('state')
    code = request.args.get('code')  # Fetch the authorization code

    if not code:
        logger.error("LINE login failed: Authorization code not received.")
        flash('LINE login failed. Please try again.', 'danger')
        return redirect(url_for('line_auth.login'))

    # Validate the state against the stored session value
    if state != session.get('oauth_state'):
        logger.error("Invalid state parameter.")
        flash('Authentication failed due to an invalid state. Please try again.', 'danger')
        return redirect(url_for('line_auth.login'))

    # Exchange the authorization code for an access token
    token_url = 'https://api.line.me/oauth2/v2.1/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': LINE_REDIRECT_URI,
        'client_id': LINE_CLIENT_ID,
        'client_secret': LINE_CLIENT_SECRET
    }
    
    logger.info(f"Token request payload: {payload}")

    try:
        token_response = requests.post(token_url, headers=headers, data=payload)
        token_data = token_response.json()

        if 'error' in token_data:
            logger.error(f"LINE token exchange error: {token_data.get('error_description', 'Unknown error')}")
            flash('LINE login failed. Please try again.', 'danger')
            return redirect(url_for('line_auth.login'))

        access_token = token_data.get('access_token')

        # Fetch user profile using the access token
        profile_url = 'https://api.line.me/v2/profile'
        profile_response = requests.get(profile_url, headers={'Authorization': f'Bearer {access_token}'})
        profile_data = profile_response.json()

        # Extract user information from LINE profile
        line_id = profile_data.get('userId')
        display_name = profile_data.get('displayName')
        email = profile_data.get('email')  # Requires additional consent from the user
        profile = pic = profile_data.get('picture_url')

        if not line_id:
            logger.error("LINE profile data missing user ID.")
            flash('LINE login failed. Please try again.', 'danger')
            return redirect(url_for('line_auth.login'))

        # Check if the user exists in the database
        user = mongo_user_find_line(line_id)  # Assuming line_id is stored as the username

        if not user:
            # Register the user if they don't exist
            userdata = {
                'line': user_id,
                'username': display_name,
                'pic': pic,
                'is_admin': False,
                'limit': 2,
            }
            user = User(userdata)
            user.create_user()
            logger.info(f"New user registered via LINE: {line_id}")

        # Log the user in
        user = User.get_user_by_line_id(line_id)
        if user:
            login_user(user)
            logger.info(f"User '{line_id}' logged in successfully via LINE.")
            return redirect(url_for('home.index'))

    except Exception as e:
        logger.error(f"Error during LINE login process: {e}")
        flash('LINE login failed. Please try again.', 'danger')

    return redirect(url_for('line_auth.login'))

@line_auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    logger.info("User logged out.")
    return redirect(url_for('line_auth.login'))