import os
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import logging
from bson import ObjectId
from bson.json_util import dumps

load_dotenv()

logging.basicConfig(
    filename='logs/mongodb_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# Environment variable setup
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASS = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

# Utility functions
def mongo_connect():
    """Create a MongoClient connection."""
    try:
        client = MongoClient(
            f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}"
        )
        return client.db  # Return the specific database
    except Exception as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        raise

def create_admin_user():
    try:
        db = mongo_connect()
        admin = db.users.find_one({'username': 'admin'})
        if not admin:
            logger.info("Admin user not found. Creating admin...")
            user_data = {
                'line': '',
                'username': 'admin',
                'password': generate_password_hash('123456', method='pbkdf2:sha256'),
                'is_admin': True,
                'parking_status': 'available',
                'license_plate': ''
            }
            
            db.users.insert_one(user_data)
            logger.info("Admin user created!")
        else:
            logger.info("Admin user already exists.")
    except Exception as e:
        logger.error(f"Error creating admin document: {e}")
        return None

def mongo_img_insert(time, value):
    try:
        db = mongo_connect()
        doc = {
            "tstamp": str(time),  # Store timestamp as string
            "uuid": str(value)  # Store UUID as string
        }
        db.imgs.insert_one(doc)
        logger.info(f"Document inserted with timestamp: {time} and UUID: {value}")

    except Exception as e:
        logger.error(f"Error inserting document: {e}")
        return None

def mongo_img_by_uuid(uuid):
    try:
        db = mongo_connect()
        doc = db.imgs.find_one({"uuid": uuid})
        logger.info(f"Queried document with UUID: {uuid}")
        return doc

    except Exception as e:
        logger.error(f"Error querying MongoDB: {e}")
        return None

def mongo_user_create(user_data):
    try:
        db = mongo_connect()
        result = db.users.insert_one(user_data)
        logger.info(f"User created with ID: {result.inserted_id}")

    except Exception as e:
        logger.error(f"Error inserting user document: {e}")
        return None

def mongo_user_find_uname(uname):
    try:
        db = mongo_connect()
        doc = db.users.find_one({"username": uname})
        logger.info(f"Queried user with username: {uname}")
        return doc

    except Exception as e:
        logger.error(f"Error querying MongoDB: {e}")
        return None
    
def mongo_user_find_id(id):
    try:
        if isinstance(id, str):
            if ObjectId.is_valid(id):
                id = ObjectId(id)
            else:
                logger.warning(f"Provided ID '{id}' is not a valid ObjectId.")
                return None

        db = mongo_connect()
        doc = db.users.find_one({"_id": id})
        logger.info(f"Queried user with ID: {id}")
        return doc

    except Exception as e:
        logger.error(f"Error querying MongoDB with ID '{id}': {e}")
        return None
    
def mongo_user_find():
    try:
        db = mongo_connect()
        docs = db.users.find()
        logger.info("Queried all users")
        return docs

    except Exception as e:
        logger.error(f"Error querying MongoDB: {e}")
        return None

def update_user_by_id(user_id, user_data):
    db = mongo_connect()
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    db.users.update_one({'_id': user_id}, {"$set" : user_data})

def delete_user_by_id(user_id):
    db = mongo_connect()
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    db.users.delete_one({'_id': user_id})