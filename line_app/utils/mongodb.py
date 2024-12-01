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

host = os.environ["MONGO_HOST"]
user = os.environ["MONGO_INITDB_ROOT_USERNAME"]
passwd = os.environ["MONGO_INITDB_ROOT_PASSWORD"]
port = 27017

def create_admin_user():
    try:
        mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
        admin = mongoClient.db.users.find_one({'username': 'admin'})
        if not admin:
            logger.info("Admin user not found. Creating admin...")
            user_data = {
                'username': 'admin',
                'password': generate_password_hash('123456', method='pbkdf2:sha256'),
                'is_admin': True,
                'parking_status': 'available',
                'license_plate': ''
            }
            
            mongoClient.db.users.insert_one(user_data)
            logger.info("Admin user created!")
        else:
            logger.info("Admin user already exists.")
    except Exception as e:
        logger.error(f"Error creating admin document: {e}")
        return None

def mongo_img_insert(time, value):
    try:
        mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
        doc = {
            "tstamp": str(time),  # Store timestamp as string
            "uuid": str(value)  # Store UUID as string
        }
        mongoClient.db.imgs.insert_one(doc)
        logger.info(f"Document inserted with timestamp: {time} and UUID: {value}")

    except Exception as e:
        logger.error(f"Error inserting document: {e}")
        return None

def mongo_img_by_uuid(uuid):
    try:
        mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
        doc = mongoClient.db.imgs.find_one({"uuid": uuid})
        logger.info(f"Queried document with UUID: {uuid}")
        return doc

    except Exception as e:
        logger.error(f"Error querying MongoDB: {e}")
        return None

def mongo_user_create(user_data):
    try:
        mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
        result = mongoClient.db.users.insert_one(user_data)
        logger.info(f"User created with ID: {result.inserted_id}")

    except Exception as e:
        logger.error(f"Error inserting user document: {e}")
        return None

def mongo_user_find_uname(uname):
    try:
        mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
        doc = mongoClient.db.users.find_one({"username": uname})
        logger.info(f"Queried user with username: {uname}")
        return doc

    except Exception as e:
        logger.error(f"Error querying MongoDB: {e}")
        return None
    
def mongo_user_find_id(id):
    try:
        # Convert `id` to `ObjectId` if it's a string
        if isinstance(id, str):
            if ObjectId.is_valid(id):  # Check if the string is a valid ObjectId
                id = ObjectId(id)
            else:
                logger.warning(f"Provided ID '{id}' is not a valid ObjectId.")
                return None

        # MongoDB connection (replace with your actual database and collection names)
        mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
        # Query for the user document
        doc = mongoClient.db.users.find_one({"_id": id})
        logger.info(f"Queried user with ID: {id}")
        return doc

    except Exception as e:
        logger.error(f"Error querying MongoDB with ID '{id}': {e}")
        return None
    
def mongo_user_find():
    try:
        mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
        docs = mongoClient.db.users.find()
        logger.info("Queried all users")
        return docs

    except Exception as e:
        logger.error(f"Error querying MongoDB: {e}")
        return None

def update_user_by_id(user_id, user_data):
    """Update a user in MongoDB by user ID."""
    mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
        # Convert user_id to ObjectId if necessary
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    mongoClient.db.users.update_one({'_id': user_id}, {"$set" : user_data})

def delete_user_by_id(user_id):
    """Delete a user from MongoDB by user ID."""
    mongoClient = MongoClient(f"mongodb://{user}:{passwd}@{host}:{port}")
    # Convert user_id to ObjectId if necessary
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    mongoClient.db.users.delete_one({'_id': user_id})