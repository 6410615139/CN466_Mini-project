from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, SubmitField, BooleanField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length, InputRequired, Optional
from wtforms import IntegerField

# Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])

# Register Form
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])

class EditUserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField(
        'Password (leave blank if unchanged)',
        validators=[Optional(), Length(min=6, max=20)]
    )
    limit = IntegerField('Limit', validators=[InputRequired()])
    is_admin = BooleanField('Admin')
    license_plates = TextAreaField(
        'License Plates (Comma-Separated)',
        validators=[Optional(), Length(max=500)],  # Adjust max length if needed
        description="Enter multiple license plates separated by commas (e.g., ABC123, XYZ789)."
    )
    submit = SubmitField('Update User')

# Add User Form
class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    limit = IntegerField('Limit', default=0)  # Set default value here
    license_plates = TextAreaField(
        'License Plates (Comma-Separated)', 
        validators=[Optional(), Length(max=500)],  # Adjust max length if needed
        description="Enter multiple license plates separated by commas (e.g., ABC123, XYZ789)."
    )
    submit = SubmitField('Create User')


class AddPlateForm(FlaskForm):
    plate_number = StringField('Plate Number', validators=[
        DataRequired(),
        Length(min=1, max=20, message="Plate number must be between 1 and 20 characters.")
    ])
    submit = SubmitField('Add Plate')