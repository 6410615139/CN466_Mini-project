# routes/admin.py
from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from functools import wraps
from werkzeug.security import generate_password_hash
from bson import ObjectId
import logging
from forms import EditUserForm, RegisterForm, AddUserForm
from models import User, LicensePlate
from utils.mongodb import mongo_parking_history

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
        users = User.get_users_with_license_plates()
        return render_template('admin_dashboard.html', users=users)
    except Exception as e:
        logging.error(f"Error fetching users for dashboard: {e}")
        return jsonify(success=False, error="Failed to fetch users"), 500

@admin_blueprint.route('/history', methods=['GET'])
@login_required
@admin_required
def history():
    try:
        history = mongo_parking_history()
        return render_template('history.html', history= history)
    except Exception as e:
        logging.error(f"Error fetching users for dashboard: {e}")
        return jsonify(success=False, error="Failed to fetch users"), 500

@admin_blueprint.route('/edit_user/<user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    # Fetch the user by ID
    user = User.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin.dashboard'))

    # Pre-fill the form with the existing user data
    form = EditUserForm(
        username=user.username,
        limit=user.limit,
        license_plates=", ".join([plate.get('plate') for plate in user.find_plate()]),
        is_admin=user.is_admin
    )

    if form.validate_on_submit():  # Process form submission
        try:
            # Extract form data
            username = form.username.data
            limit = form.limit.data
            raw_license_plates = form.license_plates.data
            is_admin = form.is_admin.data
            password = form.password.data

            # Parse license plates into a list
            license_plates = [
                plate.strip() for plate in raw_license_plates.split(',') if plate.strip()
            ]

            # If a new password is provided, hash it; otherwise, retain the current value
            if password:
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            else:
                hashed_password = user.line  # Retain the existing password

            # Create the updated user data dictionary
            user_data = {
                'line': hashed_password,
                'username': username,
                'pic': user.pic,  # Retain profile picture (if applicable)
                'is_admin': is_admin,
                'limit': limit,
            }

            # Update user data in the database
            user.edit_user(user_data)

            # Clear existing license plates and insert new ones
            current_plates = user.find_plate()
            for plate in current_plates:
                LicensePlate.remove_plate(plate.get('plate'))

            for plate in license_plates:
                plate_data = {
                    "user_id": user.id,
                    "plate": plate,
                    "status": False  # Default status
                }
                LicensePlate.add_plate(plate_data)

            flash(f"User '{username}' updated successfully.", "success")
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            logger.error(f"Error updating user '{user_id}': {e}")
            flash("An error occurred while updating the user. Please try again.", "danger")

    # Render the form template
    return render_template('edit_user.html', form=form, user=user)

@admin_blueprint.route('/delete_user/<user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    try:
        user = User.get_user_by_id(user_id)
        user.delete_user()

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
        password = form.password.data
        limit = form.limit.data
        raw_license_plates = form.license_plates.data

        # Parse license plates into a list
        license_plates = [
            plate.strip() for plate in raw_license_plates.split(',')
            if plate.strip()
        ]

        # Create user data dictionary
        user_data = {
            'password': generate_password_hash(password, method='pbkdf2:sha256'),
            'username': username,
            'pic': "",
            'is_admin': False,
            'limit': limit,
            'line': ""
        }

        # Insert new user and related license plates
        try:
            # Insert user into the users collection
            user = User(user_data)
            if not user.create_user():
                return redirect(url_for('admin.add_user'))

            # Insert license plates into the license_plates collection
            for plate in license_plates:
                plate_data = {
                    "user_id": str(user.id),
                    "plate": plate,
                    "status": False
                }
                LicensePlate.add_plate(plate_data)

            flash(f"User {username} created successfully.", "success")
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            flash("Error creating user. Please try again.", "danger")

    return render_template('add_user.html', form=form)  # Render the form on GET or invalid submission