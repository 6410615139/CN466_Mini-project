import os
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import logging
from bson import ObjectId

load_dotenv()

# Configure logging
logging.basicConfig(
    filename='logs/mongodb_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# MongoDB Connection Parameters
host = os.getenv("MONGO_HOST")
user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
passwd = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
port = 27017

def get_mongo_client():
    """Reusable MongoClient connection."""
    return MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")

# --- ADMIN FUNCTIONS ---

def create_admin_user():
    """Create an admin user if not already exists."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        admin = db.users.find_one({'username': 'admin'})
        if not admin:
            logger.info("Admin user not found. Creating admin...")
            user_data = {
                'line': "",
                'username': "admin",
                'pic': "",
                'is_admin': True,
                'limit': 9999,
            }
            db.users.insert_one(user_data)
            logger.info("Admin user created!")
        else:
            logger.info("Admin user already exists.")
    except Exception as e:
        logger.error(f"Error creating admin document: {e}")

# --- IMAGE FUNCTIONS ---

def mongo_img_insert(timestamp, uuid):
    """Insert an image document with timestamp and UUID."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        doc = {"tstamp": str(timestamp), "uuid": str(uuid)}
        db.imgs.insert_one(doc)
        logger.info(f"Image document inserted with timestamp: {timestamp}, UUID: {uuid}")
    except Exception as e:
        logger.error(f"Error inserting image document: {e}")

def mongo_img_by_uuid(uuid):
    """Find an image document by UUID."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        doc = db.imgs.find_one({"uuid": uuid})
        logger.info(f"Queried image document with UUID: {uuid}")
        return doc
    except Exception as e:
        logger.error(f"Error querying image document by UUID: {e}")
        return None

# --- USER FUNCTIONS ---

def mongo_user_create(user_data):
    """Create a new user document."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        result = db.users.insert_one(user_data)
        logger.info(f"User created with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error inserting user document: {e}")
        return None

def mongo_user_find_uname(username):
    """Find a user document by username."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        doc = db.users.find_one({"username": username})
        logger.info(f"Queried user with username: {username}")
        return doc
    except Exception as e:
        logger.error(f"Error querying user by username: {e}")
        return None

def mongo_user_find_line(line):
    """Find a user document by username."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        doc = db.users.find_one({"line": line})
        logger.info(f"Queried user with line: {line}")
        return doc
    except Exception as e:
        logger.error(f"Error querying user by line: {e}")
        return None

def mongo_user_find_id(user_id):
    """Find a user document by MongoDB ID."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        # Convert `user_id` to ObjectId if necessary
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            user_id = ObjectId(user_id)
        doc = db.users.find_one({"_id": user_id})
        logger.info(f"Queried user with ID: {user_id}")
        return doc
    except Exception as e:
        logger.error(f"Error querying user by ID: {e}")
        return None

def mongo_user_find():
    """Find all user documents."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        docs = db.users.find()
        logger.info("Queried all users.")
        return list(docs)
    except Exception as e:
        logger.error(f"Error querying all users: {e}")
        return []

def update_user_by_id(user_id, user_data):
    """Update a user document by MongoDB ID."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        # Convert user_id to ObjectId if necessary
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            user_id = ObjectId(user_id)
        result = db.users.update_one({'_id': user_id}, {"$set": user_data})
        if result.modified_count > 0:
            logger.info(f"User with ID {user_id} updated successfully.")
        else:
            logger.warning(f"No changes made to user with ID {user_id}.")
    except Exception as e:
        logger.error(f"Error updating user by ID: {e}")

def delete_user_by_id(user_id):
    """Delete a user and their associated license plates from MongoDB by user ID."""
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        # Convert user_id to ObjectId if necessary
        if isinstance(user_id, str) and ObjectId.is_valid(user_id):
            user_id = ObjectId(user_id)

        # Delete the user
        user_result = db.users.delete_one({'_id': user_id})
        if user_result.deleted_count > 0:
            logger.info(f"User with ID {user_id} deleted successfully.")

            # Delete associated license plates
            plate_result = db.license_plates.delete_many({'user_id': user_id})
            logger.info(f"Deleted {plate_result.deleted_count} license plates associated with user ID {user_id}.")
        else:
            logger.warning(f"User with ID {user_id} not found.")
    except Exception as e:
        logger.error(f"Error deleting user and associated license plates by ID: {e}")
        
def get_users_with_license_plates():
    """Fetch users and map their license plates."""
    mongoClient = get_mongo_client()
    db = mongoClient.db

    # Query users
    users = list(db.users.find())

    # Query license plates and group them by user_id
    license_plates = db.license_plates.aggregate([
        {"$group": {"_id": "$user_id", "plates": {"$push": "$plate"}}}
    ])
    license_plate_map = {item["_id"]: item["plates"] for item in license_plates}

    # Attach license plates to users
    for user in users:
        user_id = str(user["_id"])  # Convert ObjectId to string for matching
        user["license_plates"] = license_plate_map.get(user_id, [])

    return users

# --- LICENSE PLATE FUNCTIONS ---

def mongo_license_plate_find(query):
    """Find license plates matching a query."""
    mongoClient = get_mongo_client()
    try:
        db = mongoClient.db
        results = list(db.license_plates.find(query))
        return results if results else []  # Return an empty list if no results
    except Exception as e:
        logger.error(f"Error querying license plates: {e}")
        return []  # Ensure an empty list is returned in case of an error

def mongo_license_plate_insert(plate_data):
    """Insert a new license plate into the database."""
    mongoClient = get_mongo_client()
    try:
        db = mongoClient.db
        result = db.license_plates.insert_one(plate_data)
        logger.info(f"License plate inserted with ID: {result.inserted_id}")
        logger.debug(f"Inserted license plate data: {plate_data}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error inserting license plate: {e}")
        return None

def mongo_license_plate_delete(plate, user_id=None):
    """Delete a license plate from the database."""
    mongoClient = get_mongo_client()
    try:
        db = mongoClient.db
        query = {"plate": plate}
        if user_id:
            query["line"] = user_id  # Add user_id to query for precise matching
        result = db.license_plates.delete_one(query)
        if result.deleted_count > 0:
            logger.info(f"License plate '{plate}' deleted successfully.")
            return True
        else:
            logger.warning(f"License plate '{plate}' not found.")
            return False
    except Exception as e:
        logger.error(f"Error deleting license plate: {e}")
        return False