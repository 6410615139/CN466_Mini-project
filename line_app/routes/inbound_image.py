from flask import Blueprint, request, jsonify, send_from_directory, render_template, Response
import os

from dotenv import load_dotenv

load_dotenv()

import glob
import uuid
import time
from flask import request, jsonify
import paho.mqtt.client as mqtt
from utils.mongodb import mongo_img_insert
from flask_login import login_required, current_user
from routes.admin import admin_required
import threading
from io import BytesIO

inimage_blueprint = Blueprint('inimage', __name__)

latest_image = None
latest_frame = BytesIO()
frame_lock = threading.Lock()

mqtt_client = mqtt.Client()
mqtt_client.connect(os.environ("MQTT_BROKER"), os.environ("MQTT_PORT"), 60)
MQTT_SUB_TOPIC = "/inbound/#"

IMAGE_DIR = "./images"
gate1_image_folder_path = IMAGE_DIR + "/inbound/gate1/" + str(uuid.uuid4())

def on_message(client, userdata, msg):
    if msg.topic.split("/")[-1] == "gate1":
        global gate1_image_folder_path
        os.makedirs(image_folder_path, exist_ok=True)
        if msg.payload.decode('utf-8') == "disable":
            image_folder_path = IMAGE_DIR + msg.topic + str(uuid.uuid4())

mqtt_client.on_message = on_message
mqtt_client.subscribe(MQTT_SUB_TOPIC)
mqtt_client.loop_start()

@image_blueprint.route("/video", methods=["POST"])
def receive_frame():
    global image_folder_path
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    try:
        with frame_lock:
            readable_time = time.strftime("%d-%m-%y-%H:%M:%S", time.localtime(time.time()))
            filename = f"{readable_time}.jpg"
            image_file = os.path.join(image_folder_path, filename)
            with open(image_file, 'wb') as f:
                f.write(file.read())
            if not os.path.exists(image_file):
                return jsonify({"error": "Failed to save the image file"}), 500
            # else:
            #     os.excute(ai.py)
            return jsonify({"message": "Frame received successfully", "file": image_file}), 200
    except Exception as e:
        return jsonify({"error": f"Error processing frame: {e}"}), 500

######## TODO ###########

# @image_blueprint.route("/upload_image", methods=["POST"])
# def upload_image():
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400
#     try:
#         file_uuid = str(uuid.uuid4())
#         filename = f"{file_uuid}.jpg"
#         image_path = os.path.join(IMAGE_DIR, filename)
#         file.save(image_path)
        
#         timestamp = time.time()
#         local_time = time.localtime(timestamp)
#         readable_time = time.strftime("%d/%m/%y-%H:%M", local_time)
#         mongo_img_insert(readable_time, file_uuid)

#         return jsonify({"message": "Image uploaded successfully", "file_uuid": file_uuid, "timestamp": readable_time}), 200
#     except Exception as e:
#         return jsonify({"error": f"Error processing image: {e}"}), 500

# @admin_required
# @login_required
# @image_blueprint.route("/<uuid>", methods=["GET"])
# def show_image(uuid):
#     image_path = os.path.join(IMAGE_DIR, f"{uuid}.jpg")
    
#     if os.path.exists(image_path):
#         return send_from_directory(IMAGE_DIR, f"{uuid}.jpg", mimetype='image/jpeg')
#     else:
#         return jsonify({"error": "Image not found"}), 404

# @admin_required
# @login_required
# @image_blueprint.route("/image_list", methods=["GET"])
# def list_images():
#     image_files = glob.glob(os.path.join(IMAGE_DIR, "*.jpg"))
#     image_uuid = [os.path.splitext(os.path.basename(image))[0] for image in image_files]
#     viewModel = {
#         "uuid": image_uuid
#     }
#     return render_template('images_list.html', user=current_user, viewModel=viewModel)

# @admin_required
# @login_required
# @image_blueprint.route("/video_feed", methods=["GET"])
# def video_feed():
#     def generate():
#         while True:
#             with frame_lock:
#                 frame_data = latest_frame.getvalue()
#                 if frame_data:
#                     yield (b'--frame\r\n'
#                            b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
#             time.sleep(0.05)
#     return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')