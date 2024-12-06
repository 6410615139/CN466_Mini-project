# routes/admin.py
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from functools import wraps
from utils.mongodb import mongo_user_find, update_user_by_id, mongo_user_find_id, delete_user_by_id, mongo_user_create, get_users_with_license_plates, mongo_license_plate_insert
from werkzeug.security import generate_password_hash
from bson import ObjectId
import logging
from forms import EditUserForm, RegisterForm, AddUserForm
from models import User

# Initialize the Blueprint
admin_blueprint = Blueprint('admin', __name__)

# Decorator to ensure that only admins can access the route
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))  # Redirect to login if not admin
        return f(*args, **kwargs)
    return decorated_function

@admin_blueprint.route('/dashboard', methods=['GET'])
@login_required
@admin_required
def dashboard():
    try:
        users = get_users_with_license_plates()  # Fetch users with license plates
        return render_template('admin_dashboard.html', users=users)
    except Exception as e:
        logging.error(f"Error fetching users for dashboard: {e}")
        return jsonify(success=False, error="Failed to fetch users"), 500

@admin_blueprint.route('/edit_user', methods=['POST'])
@login_required
@admin_required
def edit_user():
    if not request.is_json:
        return jsonify(success=False, error="Invalid request format"), 400

    data = request.get_json()
    user_id = data.get('user_id')

    # Fetch existing user data to handle partial updates
    existing_user = mongo_user_find_id(user_id)
    if not existing_user:
        return jsonify(success=False, error="User not found"), 404

    # Check if a new password is provided; hash it if so
    new_password = data.get('password')
    if new_password and new_password != existing_user["password"]:
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
    else:
        hashed_password = existing_user["password"]

    # Convert `is_admin` to a proper boolean
    is_admin = data.get('is_admin') in ['True', 'true', True, '1', 1]

    # Prepare updated user data
    user_data = {
        'username': data.get('username', existing_user['username']),
        'password': hashed_password,
        'is_admin': is_admin,
        'parking_status': data.get('parking_status', existing_user.get('parking_status')),
        'license_plate': data.get('license_plate', existing_user.get('license_plate'))
    }

    # Update user in MongoDB
    try:
        update_user_by_id(user_id, user_data)
        return jsonify(success=True), 200
    except Exception as e:
        logging.error(f"Error updating user: {e}")
        return jsonify(success=False, error="Failed to update user"), 500

@admin_blueprint.route('/delete_user/<user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    try:
        user_id = ObjectId(user_id)
        delete_user_by_id(user_id)

        return jsonify(success=True), 200

    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify(success=False, error=str(e)), 500
    
@admin_blueprint.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = AddUserForm()  # Initialize the AddUserForm
    if form.validate_on_submit():  # Check if form is submitted and valid
        username = form.username.data
        password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        raw_license_plates = form.license_plates.data

        # Parse license plates into a list
        license_plates = [
            plate.strip() for plate in raw_license_plates.split(',')
            if plate.strip()
        ]

        # Create user data dictionary
        user_data = {
            'username': username,
            'password': password,
            'is_admin': False,  # Default new user to not be an admin
            'parking_status': None  # Default parking status to None
        }

        # Insert new user and related license plates
        try:
            # Insert user into the users collection
            user_id = mongo_user_create(user_data)

            # Insert license plates into the license_plates collection
            for plate in license_plates:
                mongo_license_plate_insert({
                    "user_id": str(user_id),
                    "plate": plate
                })

            flash(f"User {username} created successfully.", "success")
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            flash("Error creating user. Please try again.", "danger")

    return render_template('add_user.html', form=form)  # Render the form on GET or invalid submission