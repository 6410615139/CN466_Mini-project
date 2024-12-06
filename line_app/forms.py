from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, SubmitField, BooleanField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length, InputRequired, Optional

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
    # Parking status
    parking_status = BooleanField('Parking Status')
    # License plates (comma-separated input for multiple plates)
    license_plates = TextAreaField(
        'License Plates (Comma-Separated)', 
        validators=[Optional(), Length(max=500)],  # Adjust max length if needed
        description="Enter multiple license plates separated by commas (e.g., ABC123, XYZ789)."
    )
    # Submit button
    submit = SubmitField('Save Changes')

# Add User Form
class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=20)])
    # License plates (comma-separated input for multiple plates)
    license_plates = TextAreaField(
        'License Plates (Comma-Separated)', 
        validators=[Optional(), Length(max=500)],  # Adjust max length if needed
        description="Enter multiple license plates separated by commas (e.g., ABC123, XYZ789)."
    )
    submit = SubmitField('Create User')