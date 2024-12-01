import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from flask_login import LoginManager
from utils.init import create_admin_user
from models import User

from routes.auth import auth_blueprint
from routes.admin import admin_blueprint
from routes.home import home_blueprint
from routes.image import image_blueprint

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

app.register_blueprint(home_blueprint)
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(admin_blueprint, url_prefix='/admin')
app.register_blueprint(image_blueprint, url_prefix='/image')
# app.register_blueprint(liff_blueprint, url_prefix='/liff')

create_admin_user()

@login_manager.user_loader
def load_user(user_id):
    return User.get_user_by_id(user_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
