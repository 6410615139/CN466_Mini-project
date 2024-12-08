import logging
from flask import Blueprint, request, jsonify, send_from_directory, render_template, Response
import os
from dotenv import load_dotenv
load_dotenv()

import uuid
import time
import paho.mqtt.client as mqtt
import threading
from io import BytesIO

# Initialize Flask Blueprint
inimage_blueprint = Blueprint('inimage', __name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG,  # Log level (DEBUG for detailed logs)
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
                    handlers=[logging.StreamHandler()])  # Output logs to console

# Variables
IMAGE_DIR = "./images/"
os.makedirs(IMAGE_DIR, exist_ok=True)
latest_image = None
latest_frame = BytesIO()
frame_lock = threading.Lock()
current_folder_uuid = str(uuid.uuid4())

mqtt_client = mqtt.Client()
mqtt_client.connect(os.getenv("MQTT_BROKER"), int(os.getenv("MQTT_PORT")), 60)
MQTT_SUB_TOPIC = "/inbound/#"

# Callback function for when a message is received on the '/flask/car' topic
def on_message(client, userdata, msg):
    global current_folder_uuid  # Make sure to update the folder UUID when state changes
    
    payload = msg.payload.decode('utf-8')  # Decode message to string
    
    if payload == "car":
        print("Received 'car' message. Storing images in current folder.")
        # No changes needed to UUID; we continue to use the current folder
    elif payload == "free":
        # Change the folder UUID when the state transitions to "free"
        print("Received 'free' message. Changing image storage folder.")
        current_folder_uuid = str(uuid.uuid4())  # Assign a new UUID for the folder

mqtt_client.on_message = on_message
mqtt_client.subscribe(MQTT_SUB_TOPIC)
mqtt_client.loop_start()

# Route to receive frames continuously from the board
@inimage_blueprint.route("/video", methods=["POST"])
def receive_frame():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Lock the frame processing to avoid concurrent issues
        with frame_lock:
            # Create a unique directory for each image (based on current folder UUID)
            image_path = os.path.join(IMAGE_DIR, "inbound", "gate1", current_folder_uuid)

            # Ensure the directory exists, create if necessary
            os.makedirs(image_path, exist_ok=True)

            # Format the timestamp for the filename
            timestamp = time.time()
            local_time = time.localtime(timestamp)
            readable_time = time.strftime("%d-%m-%y-%H:%M:%S", local_time)

            # Create the filename using the formatted timestamp
            filename = f"{readable_time}.jpg"
            image_file = os.path.join(image_path, filename)

            # Save the uploaded file to the designated path
            with open(image_file, 'wb') as f:
                f.write(file.read())

            # Ensure the file is saved correctly
            if not os.path.exists(image_file):
                return jsonify({"error": "Failed to save the image file"}), 500

            # Respond with a success message and the file path
            return jsonify({"message": "Frame received successfully", "file": image_file}), 200
    except Exception as e:
        return jsonify({"error": f"Error processing frame: {e}"}), 500
