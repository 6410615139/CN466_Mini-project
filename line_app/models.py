import logging
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from utils.mongodb import mongo_user_find_uname, mongo_user_find_id, mongo_license_plate_find, mongo_license_plate_insert, mongo_license_plate_delete, mongo_user_create, mongo_user_find_line, update_user_by_id
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
        self.id = str(user_data.get('_id'))
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
            return cls(user_data)
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
                return cls(user_data)
            logger.warning(f"User with ID '{user_id}' not found in database.")
        except Exception as e:
            logger.error(f"Error fetching user by ID '{user_id}': {e}")
        return None
    
    @classmethod
    def get_user_by_line_id(cls, line_id):
        """Get a user by their LINE ID."""
        try:
            logger.info(f"Attempting to fetch user by LINE ID: {line_id}")
            # Query the database for a user with the given LINE ID
            user_data = mongo_user_find_line(line_id)
            if user_data:
                logger.info(f"User with LINE ID '{line_id}' found in database.")
                return cls(user_data)
            logger.warning(f"User with LINE ID '{line_id}' not found in database.")
        except Exception as e:
            logger.error(f"Error fetching user by LINE ID '{line_id}': {e}")
        return None

    def find_plate(self):
        """Find license plates associated with the user."""
        try:
            logger.info(f"Attempting to find license plates for user: {self.username}")
            plates = mongo_license_plate_find({'line': self.line})
            logger.info(f"Found {len(plates)} license plates for user '{self.username}'.")
            return plates
        except Exception as e:
            logger.error(f"Error finding license plates for user '{self.username}': {e}")
            return []

    def add_plate(self, plate_number):
        """Add a license plate to the database."""
        try:
            logger.info(f"Attempting to add license plate: {plate_number}")
            plate_data = {
                'line': self.line,
                'plate': plate_number,
                'status': False
            }
            result = mongo_license_plate_insert(plate_data)
            if result:
                logger.info(f"License plate '{plate_number}' added successfully.")
            else:
                logger.warning(f"Failed to add license plate '{plate_number}'.")
        except Exception as e:
            logger.error(f"Error adding license plate '{plate_number}': {e}")

    def remove_plate(self, plate_number):
        """Remove a license plate from the database."""
        try:
            logger.info(f"Attempting to remove license plate: {plate_number}")
            result = mongo_license_plate_delete(plate_number, user_id=self.line)
            if result:
                logger.info(f"License plate '{plate_number}' removed successfully.")
            else:
                logger.warning(f"License plate '{plate_number}' not found.")
        except Exception as e:
            logger.error(f"Error removing license plate '{plate_number}': {e}")

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

    def update_user(self):
        """Update the user in the database using the user data."""
        user_data = self.get_user_data()
        try:
            update_user_by_id(self.id, user_data)
            logger.info(f"User '{self.username}' updated successfully.")
        except Exception as e:
            logger.error(f"Error updating user '{self.username}': {e}")


class LicensePlate:
    def __init__(self, plate_data):
        """Initialize the User object using a dictionary of user data."""
        self.line = plate_data.get('line')
        self.plate = plate_data.get('plate')
        self.status = bool(user_data.get('status', False))
        logger.info(f"Initialized LicensePlate object for plate: {self.plate}")

    @classmethod
    def find_plate(plate_number):
        """Find a license plate by plate number."""
        try:
            logger.info(f"Attempting to fetch license plate: {plate_number}")
            plate_data = mongo_license_plate_find({'plate': plate_number})
            if plate_data:
                logger.info(f"License plate '{plate_number}' found in database.")
                return cls(plate_data)
            logger.warning(f"License plate '{plate_number}' not found in database.")
        except Exception as e:
            logger.error(f"Error fetching license plate '{plate_number}': {e}")
        return None

    @classmethod
    def find_plate_line(line):
        """Find a license plate by line."""
        try:
            logger.info(f"Attempting to fetch license plate by line: {line}")
            plate_data = mongo_license_plate_find({'line': line})
            if plate_data:
                logger.info(f"License plate with line '{line}' found in database.")
                return cls(plate_data)
            logger.warning(f"License plate with line '{line}' not found in database.")
        except Exception as e:
            logger.error(f"Error fetching license plate by line '{line}': {e}")
        return None

    @classmethod
    def add_plate(cls, plate_data):
        """Add a new license plate to the database."""
        try:
            lp = find_plate({'plate': plate_data['plate']})
            if lp:
                logger.warning(f"License plate '{plate_data['plate']}' already exists in database.")
                return None
            logger.info(f"Adding license plate: {plate_data['plate']}")
            mongo_license_plate_insert(plate_data)
            logger.info(f"License plate '{plate_data['plate']}' added successfully.")
            return cls(plate_data)
        except Exception as e:
            logger.error(f"Error adding license plate '{plate_data['plate']}': {e}")
            return None

    @staticmethod
    def remove_plate(plate, user_id=None):
        """Remove a license plate."""
        try:
            logger.info(f"Removing license plate: {plate}")
            result = mongo_license_plate_delete(plate, user_id=user_id)
            if result:
                logger.info(f"License plate '{plate}' removed successfully.")
            else:
                logger.warning(f"License plate '{plate}' not found in database.")
        except Exception as e:
            logger.error(f"Error removing license plate '{plate}': {e}")

    def get_plate_data(self):
        """Return the license plate data dictionary."""
        return {
            'line': self.line,
            'plate': self.plate,
            'status': self.status,
        }
    
    def set_status(self, status):
        """Set the status of the license plate."""
        if self.status == status:
            logger.info(f"Status of license plate '{self.plate}' is already {status}")
            return
        else:
            self.status = status
            self.update_plate()
            logger.info(f"Status of license plate '{self.plate}' set to {status}")
            user = User.get_user_by_line_id(self.line)
            if status == True:
                if user.limit > 0:
                    user.limit -= 1
                    user.update_user()
                else:
                    logger.info(f"Limit of user '{user.username}' decreased to {user.limit}")
            else:
                user.limit += 1
                user.update_user()
                logger.info(f"Limit of user '{user.username}' increased to {user.limit}")

    def update_plate(self):
        """Update the license plate in the database."""
        plate_data = self.get_plate_data()
        try:
            mongo_license_plate_insert(plate_data)
            logger.info(f"License plate '{self.plate}' updated successfully.")
        except Exception as e:
            logger.error(f"Error updating license plate '{self.plate}': {e}")