import logging
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from utils.mongodb import mongo_user_find_uname, mongo_user_find_id
from bson import ObjectId

# Configure logging
logging.basicConfig(
    filename='logs/user_log.txt',  # Path to log file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

class User(UserMixin):
    def __init__(self, user_id, is_admin, username, password, parking_status, license_plate):
        self.id = user_id
        self.is_admin = is_admin
        self.username = username
        self.password = password
        self.parking_status = parking_status
        self.license_plate = license_plate
        logger.info(f"Initialized User object for username: {username}")

    @classmethod
    def get_user_by_username(cls, username):
        logger.info(f"Attempting to fetch user by username: {username}")
        user_data = mongo_user_find_uname(username)
        if user_data:
            logger.info(f"User '{username}' found in database.")
            return cls(user_id=str(user_data['_id']),
                       is_admin=user_data['is_admin'],
                       username=user_data['username'],
                       password=user_data['password'],
                       parking_status=user_data['parking_status'],
                       license_plate=user_data['license_plate'])
        logger.warning(f"User '{username}' not found in database.")
        return None

    @classmethod
    def get_user_by_id(cls, user_id):
        """Get a user by their MongoDB '_id'"""
        try:
            logger.info(f"Attempting to fetch user by ID: {user_id}")
            # Convert `user_id` to `ObjectId`
            user_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
            user_data = mongo_user_find_id(user_id)
            if user_data:
                logger.info(f"User with ID '{user_id}' found in database.")
                return cls(user_id=str(user_data['_id']),
                           is_admin=user_data['is_admin'],
                           username=user_data['username'],
                           password=user_data['password'],
                           parking_status=user_data['parking_status'],
                           license_plate=user_data['license_plate'])
            logger.warning(f"User with ID '{user_id}' not found in database.")
        except Exception as e:
            logger.error(f"Error fetching user by ID '{user_id}': {e}")
        return None

    def get_id(self):
        logger.debug(f"Returning ID for user '{self.username}': {self.id}")
        return self.id  # Return self.id for Flask-Login compatibility

    def check_password(self, password):
        """Check the hashed password."""
        result = check_password_hash(self.password, password)
        if result:
            logger.info(f"Password check for user '{self.username}' succeeded.")
        else:
            logger.warning(f"Password check for user '{self.username}' failed.")
        return result
