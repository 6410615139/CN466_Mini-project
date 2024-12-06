import logging
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from utils.mongodb import get_mongo_client, mongo_user_create
from models import User

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASS = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

def create_admin_user():
    try:
        mongoClient = get_mongo_client()
        db = mongoClient.db
        admin = db.users.find_one({'username': 'admin'})
        
        if not admin:
            logger.info("Admin user not found. Creating admin...")
            
            # Admin user data
            user_data = {
                'line': '',
                'username': 'admin',
                'password': generate_password_hash('123456', method='pbkdf2:sha256'),
                'is_admin': True,
                'parking_status': 'available',
                'license_plate': ''
            }
            
            # Create User object (if necessary)
            user = User(user_data)
            
            # Insert user data into MongoDB
            db.users.insert_one(user_data)
            
            logger.info("Admin user created successfully!")
        else:
            logger.info("Admin user already exists.")
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        return None
