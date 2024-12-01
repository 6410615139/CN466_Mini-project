from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from utils import mongodb
from utils.mongodb import update_user_by_id
from werkzeug.security import generate_password_hash
from forms import EditUserForm

home_blueprint = Blueprint('home', __name__)

# Route to display the home page
@home_blueprint.route('/')
@login_required
def index():
    return render_template('home.html', user=current_user)

# Route to edit user data
@home_blueprint.route('/edit_user', methods=['GET', 'POST'])
@login_required
def edit_user():
    form = EditUserForm()

    if form.validate_on_submit():
        # Get the current user's password, or set a new one if changed
        password = current_user.password
        if form.password.data != password:
            password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        
        # Set admin status based on form input
        is_admin = form.is_admin.data
        if form.is_admin.data in ['True', 'true', True, '1', 1]:
            is_admin = True
        else:
            is_admin = False

        # Prepare the updated user data
        user_data = {
            'username': form.username.data,  # Correcting this to update username
            'password': password,
            'is_admin': is_admin,
            'parking_status': form.parking_status.data,
            'license_plate': form.license_plate.data
        }

        # Update user data in the database
        try:
            # Assuming update_user_by_id is a function that updates the user in MongoDB
            update_user_by_id(current_user.get_id(), user_data)
            return redirect(url_for('home.index'))  # Redirect back to the home page after updating
        except Exception as e:
            print("Error updating user:", e)  # Debugging output for server log
            return jsonify(success=False, error=str(e)), 500

    return render_template('edit_user.html', user=current_user, form=form)
