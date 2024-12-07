import logging
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from utils.mongodb import mongo_user_find_uname, mongo_user_find_id, mongo_license_plate_find, mongo_license_plate_insert, mongo_license_plate_delete, mongo_user_create
from bson import ObjectId

# Configure logging
logging.basicConfig(
    filename='logs/system_log.txt',  # Path to log file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

class User(UserMixin):
    def __init__(self, user_data):
        """Initialize the User object using a dictionary of user data."""
        self.line = user_data.get('line')
        self.username = user_data.get('username')
        self.pic = user_data.get('pic')
        self.is_admin = bool(user_data.get('is_admin', False))
        self.limit = user_data.get('limit', 0)
        logger.info(f"Initialized User object for username: {self.username}")

    @classmethod
    def get_user_by_username(cls, username):
        logger.info(f"Attempting to fetch user by username: {username}")
        user_data = mongo_user_find_uname(username)
        if user_data:
            logger.info(f"User '{username}' found in database.")
            return cls(user_id=str(user_data['_id']),
                       is_admin=user_data['is_admin'],
                       username=user_data['username'],
                       password=user_data['password'])
        logger.warning(f"User '{username}' not found in database.")
        return None

    @classmethod
    def get_user_by_id(cls, user_id):
        """Get a user by their MongoDB '_id'."""
        try:
            logger.info(f"Attempting to fetch user by ID: {user_id}")
            user_id = ObjectId(user_id) if isinstance(user_id, str) and ObjectId.is_valid(user_id) else user_id
            user_data = mongo_user_find_id(user_id)
            if user_data:
                logger.info(f"User with ID '{user_id}' found in database.")
                return cls(user_id=str(user_data['_id']),
                           is_admin=user_data['is_admin'],
                           username=user_data['username'],
                           password=user_data['password'])
            logger.warning(f"User with ID '{user_id}' not found in database.")
        except Exception as e:
            logger.error(f"Error fetching user by ID '{user_id}': {e}")
        return None

    def get_id(self):
        logger.debug(f"Returning ID for user '{self.username}': {self.id}")
        return self.id  # Return self.id for Flask-Login compatibility

    def get_user_data(self):
        """Return the user data dictionary."""
        return {
            'line': self.line,
            'username': self.username,
            'pic': self.pic,
            'is_admin': self.is_admin,
            'limit': self.limit,
        }

    def create_user(self):
        """Create the user in the database using the user data."""
        user_data = self.get_user_data()
        try:
            mongo_user_create(user_data)
            logger.info(f"User '{self.username}' created successfully.")
        except Exception as e:
            logger.error(f"Error creating user '{self.username}': {e}")


class LicensePlate:
    @staticmethod
    def find_plate(plate):
        """Check if a license plate exists in the database."""
        logger.info(f"Checking for license plate: {plate}")
        plate_data = mongo_license_plate_find(plate)
        if plate_data:
            logger.info(f"License plate '{plate}' found.")
            return plate_data
        logger.warning(f"License plate '{plate}' not found.")
        return None

    @staticmethod
    def add_plate(user_id, plate, vehicle_type=None):
        """Add a new license plate for a user."""
        try:
            logger.info(f"Adding license plate '{plate}' for user ID '{user_id}'")
            new_plate = {
                "user_id": ObjectId(user_id),
                "plate": plate,
                "vehicle_type": vehicle_type
            }
            mongo_license_plate_insert(new_plate)
            logger.info(f"License plate '{plate}' added successfully.")
        except Exception as e:
            logger.error(f"Error adding license plate '{plate}' for user ID '{user_id}': {e}")

    @staticmethod
    def remove_plate(plate):
        """Remove a license plate."""
        try:
            logger.info(f"Removing license plate: {plate}")
            result = mongo_license_plate_delete(plate)
            if result:
                logger.info(f"License plate '{plate}' removed successfully.")
            else:
                logger.warning(f"License plate '{plate}' not found in database.")
        except Exception as e:
            logger.error(f"Error removing license plate '{plate}': {e}")