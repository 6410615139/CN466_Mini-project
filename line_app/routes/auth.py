# routes/auth.py

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from models import User
from werkzeug.security import generate_password_hash
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

        if user and user.check_password(password):
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
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        userdata = {
            'username': username,
            'password': hashed_password,
            'is_admin': False,
            'parking_status': 'available',
            'license_plate': ''
        }
        mongo_user_create(userdata)
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
