from flask import Blueprint, request, jsonify, send_from_directory, render_template, Response
import os
import glob
import uuid
import time
import os
import uuid
import time
from flask import request, jsonify
import paho.mqtt.client as mqtt
from utils.mongodb import mongo_img_insert
from flask_login import login_required, current_user
from routes.admin import admin_required
import threading
from io import BytesIO

# Initialize the blueprint for image handling
image_blueprint = Blueprint('image', __name__)

# Directory to store uploaded images
IMAGE_DIR = "./images/"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Store the latest image
latest_image = None

# Store the latest frame in memory
latest_frame = BytesIO()
frame_lock = threading.Lock()  # Lock to prevent race conditions on `latest_frame`

current_folder_uuid = str(uuid.uuid4())  # Initial UUID folder name

# MQTT client setup
mqtt_client = mqtt.Client()
mqtt_client.connect("mqtt.eclipseprojects.io", 1883, 60)

# Callback function for when a message is received on the '/flask/car' topic
def on_message(client, userdata, msg):
    global current_folder_uuid  # Make sure to update the folder UUID when state changes
    
    payload = msg.payload.decode('utf-8')  # Decode message to string
    
    if payload == "enable":
        print("Received 'car' message. Storing images in current folder.")
        # No changes needed to UUID; we continue to use the current folder
    elif payload == "disable":
        # Change the folder UUID when the state transitions to "free"
        print("Received 'free' message. Changing image storage folder.")
        current_folder_uuid = str(uuid.uuid4())  # Assign a new UUID for the folder

# Subscribe to the '/flask/car' topic
mqtt_client.on_message = on_message
mqtt_client.subscribe("/inbound/gate1")

# Start MQTT client loop in the background
mqtt_client.loop_start()


# Upload image route
@image_blueprint.route("/upload_image", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    try:
        file_uuid = str(uuid.uuid4())
        filename = f"{file_uuid}.jpg"
        image_path = os.path.join(IMAGE_DIR, filename)
        file.save(image_path)
        
        # Save timestamp and file UUID to MongoDB
        timestamp = time.time()
        local_time = time.localtime(timestamp)
        readable_time = time.strftime("%d/%m/%y-%H:%M", local_time)
        mongo_img_insert(readable_time, file_uuid)

        return jsonify({"message": "Image uploaded successfully", "file_uuid": file_uuid, "timestamp": readable_time}), 200
    except Exception as e:
        return jsonify({"error": f"Error processing image: {e}"}), 500

# View image route
@admin_required
@login_required
@image_blueprint.route("/<uuid>", methods=["GET"])
def show_image(uuid):
    image_path = os.path.join(IMAGE_DIR, f"{uuid}.jpg")
    
    if os.path.exists(image_path):
        return send_from_directory(IMAGE_DIR, f"{uuid}.jpg", mimetype='image/jpeg')
    else:
        return jsonify({"error": "Image not found"}), 404

# List images route
@admin_required
@login_required
@image_blueprint.route("/image_list", methods=["GET"])
def list_images():
    image_files = glob.glob(os.path.join(IMAGE_DIR, "*.jpg"))
    image_uuid = [os.path.splitext(os.path.basename(image))[0] for image in image_files]
    viewModel = {
        "uuid": image_uuid
    }
    return render_template('images_list.html', user=current_user, viewModel=viewModel)

# Route to receive frames continuously from the board
@image_blueprint.route("/video", methods=["POST"])
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
            image_path = os.path.join(IMAGE_DIR, current_folder_uuid)

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

# Route to stream the received frames as a video feed
@admin_required
@login_required
@image_blueprint.route("/video_feed", methods=["GET"])
def video_feed():
    def generate():
        while True:
            # Lock access to the latest frame to avoid race conditions
            with frame_lock:
                # Only yield the latest frame if it's not empty
                frame_data = latest_frame.getvalue()
                if frame_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

            # Small sleep interval to simulate video frame rate
            time.sleep(0.05)  # Adjust this delay as needed for frame rate

    # Return the frames in a stream format
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')