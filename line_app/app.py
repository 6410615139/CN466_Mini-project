import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from utils.mongodb import create_admin_user
from models import User

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Set Flask secret key from environment variable or default
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

create_admin_user()


# Import blueprints
from routes.auth import auth_blueprint
from routes.admin import admin_blueprint
from routes.home import home_blueprint
from routes.inbound_image import inimage_blueprint
from routes.line import line_blueprint
from routes.line_auth import line_auth_blueprint

# Register blueprints
app.register_blueprint(home_blueprint)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(admin_blueprint, url_prefix='/admin')
app.register_blueprint(inbound_image, url_prefix='/inimage')
app.register_blueprint(line_blueprint, url_prefix='/line')
app.register_blueprint(line_auth_blueprint, url_prefix='/line_auth')

# Create the admin user if it doesn't exist
create_admin_user()

# Define user_loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load a user from the database by their user_id."""
    return User.get_user_by_id(user_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
