import os
from dotenv import load_dotenv

load_dotenv()

import uuid
import time
import paho.mqtt.client as mqtt
import threading
import subprocess
from io import BytesIO
from flask import Blueprint, request, jsonify
from models import LicensePlate

inimage_blueprint = Blueprint('inimage', __name__)

IMAGE_DIR = "./images/inbound/gate1"
os.makedirs(IMAGE_DIR, exist_ok=True)
latest_image = None
latest_frame = BytesIO()
frame_lock = threading.Lock()
current_folder_uuid = str(uuid.uuid4())
mqtt_client = mqtt.Client()
mqtt_client.connect(os.getenv("MQTT_BROKER"), int(os.getenv("MQTT_PORT")), 60)
mqtt_topic = "/inbound/#"

def on_message(client, userdata, msg):
    global current_folder_uuid
    payload = msg.payload.decode('utf-8')
    if payload == "enable":
        current_folder_uuid = str(uuid.uuid4())

mqtt_client.on_message = on_message
mqtt_client.subscribe(mqtt_topic)
mqtt_client.loop_start()

def check_lp(image_file):
    try:
        # Run the ai.py script to analyze the image
        result = subprocess.run(
            ["python", "utils/ai.py", "-p", image_file],
            text=True,
            capture_output=True,
            check=True
        )

        # Capture the output of ai.py
        plate_number = result.stdout.strip().split('\n')[0]
        if not plate_number:
            return jsonify({"error": "No license plate detected in the image."}), 400

        # Find the license plate in the database
        lp = LicensePlate.find_plate(plate_number)
        if lp is None:
            return jsonify({"error": f"License plate '{plate_number}' not found in the database."}), 404

        # Update the license plate status
        if lp.set_status(True):
            mqtt_client.publish("/inbound/gate1", "disable")
            return jsonify({
                "message": "License plate detected and updated successfully.",
                "plate_number": plate_number
            }), 200
        else:
            return jsonify({"error": "Failed to update license plate status."}), 500

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Error running ai.py: {e.stderr}"}), 500

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@inimage_blueprint.route("/video", methods=["POST"])
def receive_frame():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    try:
        with frame_lock:
            image_path = os.path.join(IMAGE_DIR, current_folder_uuid)
            os.makedirs(image_path, exist_ok=True)
            timestamp = time.time()
            local_time = time.localtime(timestamp)
            readable_time = time.strftime("%d-%m-%y-%H:%M:%S", local_time)
            filename = f"{readable_time}.jpg"
            image_file = os.path.join(image_path, filename)
            with open(image_file, 'wb') as f:
                f.write(file.read())
            if not os.path.exists(image_file):
                return jsonify({"error": "Failed to save the image file"}), 500
            return check_lp(image_file)
    except Exception as e:
        return jsonify({"error": f"Error processing frame: {e}"}), 500