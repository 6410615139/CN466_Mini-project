from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from forms import EditUserForm
from forms import AddPlateForm
from models import User, LicensePlate

home_blueprint = Blueprint('home', __name__)

# Route to display the home page
@home_blueprint.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = AddPlateForm()
    user = User.get_user_by_id(current_user.id)

    # Handle adding a license plate
    if form.validate_on_submit():
        plate_number = form.plate_number.data
        if user.add_plate(plate_number):
            flash(f"License plate '{plate_number}' added successfully.", "success")
        else:
            flash(f"Failed to add license plate '{plate_number}'. It might already exist.", "danger")
        return redirect(url_for('home.index'))

    admin = user.is_admin
    if not admin:
        license_plates = user.find_plate()
    else:
        license_plates = LicensePlate.get_plates_with_user_data()

    return render_template('home.html', user=user, license_plates=license_plates, form=form, admin=admin)

# Route to handle plate deletion
@home_blueprint.route('/delete_plate/<plate>', methods=['POST'])
@login_required
def delete_plate(plate):
    user = User.get_user_by_id(current_user.id)
    if user.is_admin:
        user.remove_plate(plate_number=plate)
    if user.remove_plate(plate):
        flash(f"License plate '{plate}' deleted successfully.", "success")
    else:
        flash(f"Failed to delete license plate '{plate}'. It might not exist.", "danger")
    return redirect(url_for('home.index'))