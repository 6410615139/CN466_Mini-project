import logging
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from bson import ObjectId
from utils.mongodb import (
    mongo_user_find_uname, 
    mongo_user_find_id,
    mongo_license_plate_find_line,
    mongo_license_plate_find_plate,
    mongo_license_plate_insert, 
    mongo_license_plate_delete,
    mongo_license_plate_update_status,
    mongo_user_create, 
    mongo_user_find_line, 
    update_user_by_id,
    mongo_parking_inbound,
    mongo_parking_outbound
    )

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
            plates = mongo_license_plate_find_line(self.line)
            logger.info(f"Found {len(plates)} license plates for user '{self.username}'.")
            return plates
        except Exception as e:
            logger.error(f"Error finding license plates for user '{self.username}': {e}")
            return []

    def add_plate(self, plate_number):
        """Add a license plate to the database."""
        try:
            logger.info(f"Attempting to add license plate: {plate_number}")

            # Check if the plate already exists
            existing_plate = mongo_license_plate_find_plate(plate_number)
            if existing_plate:
                logger.warning(f"License plate '{plate_number}' already exists in the database.")
                return f"License plate '{plate_number}' already exists."

            # If it does not exist, insert it
            plate_data = {
                'line': self.line,
                'plate': plate_number,
                'status': False
            }
            result = mongo_license_plate_insert(plate_data)
            if result:
                logger.info(f"License plate '{plate_number}' added successfully.")
                return f"License plate '{plate_number}' added successfully."
            else:
                logger.warning(f"Failed to add license plate '{plate_number}'.")
                return f"Failed to add license plate '{plate_number}'."
        except Exception as e:
            logger.error(f"Error adding license plate '{plate_number}': {e}")
            return f"Error adding license plate '{plate_number}': {e}"


    def remove_plate(self, plate_number):
        """Remove a license plate from the database."""
        try:
            logger.info(f"Attempting to remove license plate: {plate_number}")
            result = mongo_license_plate_delete(plate_number, self.line)
            if result:
                logger.info(f"License plate '{plate_number}' removed successfully.")
                return f"License plate '{plate_number}' removed successfully."
            else:
                logger.warning(f"License plate '{plate_number}' not found.")
                return f"License plate '{plate_number}' not found."
        except Exception as e:
            logger.error(f"Error removing license plate '{plate_number}': {e}")
            return f"Error removing license plate '{plate_number}': {e}"

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

    def minus_limit(self):
        """Decrease the user's limit by 1."""
        try:
            if self.limit > 0:
                self.limit -= 1
                self.update_user()
                logger.info(f"User '{self.username}' limit decreased. New limit: {self.limit}")
                return True
            else:
                logger.warning(f"User '{self.username}' limit is already at 0.")
                return False
        except Exception as e:
            logger.error(f"Error decreasing user '{self.username}' limit: {e}")
            return False
    
    def plus_limit(self):
        """Increase the user's limit by 1."""
        try:
            self.limit += 1
            self.update_user()
            logger.info(f"User '{self.username}' limit increased. New limit: {self.limit}")
            return True
        except Exception as e:
            logger.error(f"Error increasing user '{self.username}' limit: {e}")
            return False


class LicensePlate:
    def __init__(self, plate_data):
        """Initialize the LicensePlate object using a dictionary of plate data."""
        try:
            logger.info(f"Initializing LicensePlate object with data: {plate_data}")
            self.id = str(plate_data.get('_id'))
            self.line = plate_data.get('line')
            self.plate = plate_data.get('plate')
            self.status = bool(plate_data.get('status', False))
            logger.info(f"Initialized LicensePlate object for plate: {self.plate}")
        except Exception as e:
            logger.error(f"Error initializing LicensePlate object: {e}")
            raise

    @classmethod
    def find_plate(cls, plate_number):
        """Find a license plate by plate number."""
        try:
            logger.info(f"Attempting to fetch license plate by plate number: {plate_number}")
            plate_data = mongo_license_plate_find_plate(plate_number)
            logger.info(f"Fetched plate data: {plate_data}")  # Log fetched data
            
            if plate_data:
                logger.info(f"License plate with plate number '{plate_number}' found in database.")
                instance = cls(plate_data)  # Attempt to create an instance
                logger.info(f"Created LicensePlate instance: {instance.__dict__}")  # Log instance attributes
                return instance
            else:
                logger.warning(f"License plate with plate number '{plate_number}' not found in database.")
        except Exception as e:
            logger.error(f"Error fetching license plate by plate number '{plate_number}': {e}")
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
        try:
            # Check if the status is already set
            if self.status == status:
                logger.info(f"Status of license plate '{self.plate}' is already {status}.")
                return False  # No change needed, return False

            # Get the user associated with the license plate
            user = User.get_user_by_line_id(self.line)
            if not user:
                logger.error(f"User associated with license plate '{self.plate}' not found.")
                return False  # Return False if no user found

            logger.info(f"Updating status for license plate '{self.plate}' to {status}.")
            logger.info(f"User '{user.username}' current limit: {user.limit}")

            if status:  # Status is being set to True (entry)
                # Attempt to decrement the user's limit
                if user.minus_limit():
                    self.status = status
                    if not mongo_license_plate_update_status(self.plate, self.status):
                        logger.error(f"Failed to update status of license plate '{self.plate}'. Reverting limit change.")
                        user.plus_limit()  # Revert the limit decrement
                        return False
                    # Log inbound parking
                    mongo_parking_inbound(self.plate)
                    logger.info(f"Status of license plate '{self.plate}' set to {status} for inbound parking.")
                else:
                    logger.warning(f"User '{user.username}' has no remaining limit to enter parking.")
                    return False
            else:  # Status is being set to False (exit)
                logger.info(f"User '{user.username}' is exiting parking. Updating limit.")
                # Attempt to increment the user's limit
                if user.plus_limit():
                    self.status = status
                    if not mongo_license_plate_update_status(self.plate, self.status):
                        logger.error(f"Failed to update status of license plate '{self.plate}'. Reverting limit change.")
                        user.minus_limit()  # Revert the limit increment
                        return False
                    # Log outbound parking
                    mongo_parking_outbound(self.plate)
                    logger.info(f"Status of license plate '{self.plate}' set to {status} for outbound parking.")
                else:
                    logger.error(f"Failed to update user limit for '{user.username}'.")
                    return False

            return True  # Successfully updated the status

        except Exception as e:
            logger.error(f"Error setting status for license plate '{self.plate}': {e}")
            return False  # Return False on exception
