# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, InputRequired, Optional
from wtforms import StringField, PasswordField

# Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])

# Register Form
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])

class EditUserForm(FlaskForm):
    user_id = HiddenField('User ID')
    # Username with validation for length
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    # Password field, made optional and hashed in the backend
    password = StringField('Password', validators=[Optional(), Length(min=6, max=25)])
    # Admin status as a Boolean field (checkbox for True/False)
    is_admin = BooleanField('Admin Status')
    # Parking status and license plate are optional
    parking_status = StringField('Parking Status', validators=[Optional()])
    license_plate = StringField('License Plate', validators=[Optional()])
    # Submit button
    submit = SubmitField('Save Changes')

# Add User Form
class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    license_plate = StringField('License Plate', validators=[Optional(), Length(max=15)])
    submit = SubmitField('Create User')
