from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from utils.mongodb import update_user_by_id, mongo_license_plate_insert, mongo_license_plate_delete, mongo_license_plate_find, mongo_license_plate_find
from werkzeug.security import generate_password_hash
from forms import EditUserForm

home_blueprint = Blueprint('home', __name__)

# Route to display the home page
@home_blueprint.route('/')
@login_required
def index():
    # Fetch license plates for the current user
    license_plates = mongo_license_plate_find({"user_id": str(current_user.id)})

    # Extract the plate values from the results
    plates = [plate["plate"] for plate in license_plates]

    return render_template('home.html', user=current_user, license_plates=plates)

# Route to edit user data
@home_blueprint.route('/edit_user', methods=['GET', 'POST'])
@login_required
def edit_user():
    form = EditUserForm()

    if form.validate_on_submit():
        # Get the current user's existing data
        current_user_data = {
            "username": current_user.username,
            "password": current_user.password,
            "is_admin": current_user.is_admin,
            "parking_status": current_user.parking_status,
        }

        # Retain current values if the form fields are empty
        username = form.username.data or current_user_data["username"]
        password = form.password.data
        if not password:  # If password is blank, keep the existing hashed password
            password = current_user_data["password"]
        else:  # If password is provided, hash the new password
            password = generate_password_hash(password, method='pbkdf2:sha256')

        is_admin = form.is_admin.data if form.is_admin.data is not None else current_user_data["is_admin"]
        parking_status = form.parking_status.data or current_user_data["parking_status"]

        # Handle license plates (retain current if blank)
        license_plates = []
        if form.license_plates.data:
            license_plates = [plate.strip() for plate in form.license_plates.data.split(',') if plate.strip()]
        else:
            # Fetch existing license plates if the input is blank
            existing_license_plates = mongo_license_plate_find({"user_id": current_user.get_id()})
            license_plates = [plate['plate'] for plate in existing_license_plates]

        # Update license plates in the database
        try:
            current_license_plates = mongo_license_plate_find({"user_id": current_user.get_id()})
            current_plate_set = set(plate['plate'] for plate in current_license_plates)
            new_plate_set = set(license_plates)

            # Add new plates
            for plate in new_plate_set - current_plate_set:
                mongo_license_plate_insert({"user_id": current_user.get_id(), "plate": plate})

            # Remove old plates
            for plate in current_plate_set - new_plate_set:
                mongo_license_plate_delete(plate)
        except Exception as e:
            print(f"Error updating license plates: {e}")
            return jsonify(success=False, error="Failed to update license plates."), 500

        # Update user data in the database
        user_data = {
            "username": username,
            "password": password,
            "is_admin": is_admin,
            "parking_status": parking_status,
        }
        try:
            update_user_by_id(current_user.get_id(), user_data)
            return redirect(url_for('home.index'))
        except Exception as e:
            print(f"Error updating user: {e}")
            return jsonify(success=False, error="Failed to update user."), 500

    # Prepopulate the form with the current user's data
    form.username.data = current_user.username
    form.parking_status.data = current_user.parking_status
    form.is_admin.data = current_user.is_admin
    try:
        current_license_plates = mongo_license_plate_find({"user_id": current_user.get_id()})
        form.license_plates.data = ', '.join([plate['plate'] for plate in current_license_plates])
    except Exception as e:
        print(f"Error fetching license plates: {e}")
        form.license_plates.data = ''

    return render_template('edit_user.html', user=current_user, form=form)