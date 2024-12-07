import os
from dotenv import load_dotenv

load_dotenv()

from datetime import datetime 
from flask import request, abort, Blueprint
import json

from linebot import LineBotApi
from linebot.exceptions import LineBotApiError

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    ImageMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# from utils.mongodb import mongo_history_insert
from utils.mongodb import mongo_user_find_line, mongo_license_plate_insert, mongo_license_plate_delete, mongo_license_plate_find
from models import User

line_blueprint = Blueprint('line', __name__)

configuration = Configuration(access_token=os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])
line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])

@line_blueprint.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # collect_user_command(event)
    if not exist_user(event):
        if event.message.text == "#create_user":
            reply_text = create_user(event)
        else:
            reply_text = "Please register first.\n(type \"#create_user\")"
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
    else:
        create_reply(event)

def collect_user_command(event):
    user_id = event.source.user_id
    timestamp = event.timestamp
    user_message = event.message.text
    timestamp_int = int(timestamp)
    covert_time = datetime.fromtimestamp(timestamp_int/1000)
    format_time = covert_time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        profile = line_bot_api.get_profile(user_id)
        display_name = profile.display_name
        pic_url = profile.picture_url
    except LineBotApiError as e:
        display_name = "Unknown"
        pic_url = None
        print(f"Error fetching user profile: {e}")
    user_data = {
        'user_id': user_id,
        'timestamp': format_time ,
        'name': display_name,
        'picture': pic_url,
        'command': user_message
    }
    # mongo_user_insert(user_data)

def exist_user(event):
    user_id = event.source.user_id
    exist = mongo_user_find_line(user_id)
    if exist:
        return True
    else:
        return False

def create_user(event):
    user_id = event.source.user_id
    profile = line_bot_api.get_profile(user_id)
    display_name = profile.display_name
    pic = profile.picture_url
    userdata = {
        'line': user_id,
        'username': display_name,
        'pic': pic,
        'is_admin': False,
        'limit': 2,
    }
    user = User(userdata)
    user.create_user()

    return f"user {display_name} created"

def create_reply(event):
    user_message = event.message.text
    if user_message == "#liff":
        command_liff(event)
    elif user_message.startswith("#lp"):
        command_lp(event)
    elif user_message == "#profile" or user_message == "#create_user":
        command_profile(event)
    else:
        command_else(event)

def command_else(event):
    user_message = event.message.text
    reply_text = f"You said: {user_message}"
    with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )

def command_profile(event):
    user_message = event.message.text
    user_data = mongo_user_find_line(event.source.user_id)
    if user_data:
        if user_message == "#create_user":
            reply_text = f"User already created...\n\n"
        reply_text = f"Profile Details:\n"
        reply_text += f"ID: {user_data['line']}\n"
        reply_text += f"Username: {user_data['username']}\n"
        reply_text += f"Admin Status: {'Yes' if user_data['is_admin'] else 'No'}\n"
        reply_text += f"Limit: {user_data['limit']}\n"
    else:
        reply_text = "User profile not found."

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[ImageMessage(original_content_url=user_data['pic'], preview_image_url=user_data['pic']),
                TextMessage(text=reply_text)]
            )
        )

def command_lp(event):
    user_message = event.message.text
    user_data = mongo_user_find_line(event.source.user_id)
    if user_data:
        command = user_message.split(" ")[1]
        if command == "add":
            plate_number = user_message.split(" ")[2]
            if plate_number:
                plate_data = {
                    "line": user_data['line'],
                    "plate": plate_number,
                    "status": False
                }
                result = mongo_license_plate_insert(plate_data)
                if result:
                    reply_text = f"License plate {plate_number} has been added to your account."
                else:
                    reply_text = "There was an error adding the license plate. Please try again."
            else:
                reply_text = "Please provide a valid license plate number after '#lp add <lp>'."
        
        elif command == "remove":
            plate_number = user_message.split(" ")[2]
            if plate_number:
                # Ensure the plate is associated with the user's line_id before removing
                plate_data = mongo_license_plate_find({"line": user_data['line'], "plate": plate_number})
                
                if plate_data:
                    # Proceed with deletion if the plate exists for this user
                    result = mongo_license_plate_delete(plate_number, user_id=user_data['line'])
                    if result:
                        reply_text = f"License plate {plate_number} has been removed from your account."
                    else:
                        reply_text = f"Error removing license plate {plate_number}. Please try again."
                else:
                    reply_text = f"License plate {plate_number} not found or is not associated with your account."
            else:
                reply_text = "Please provide a valid license plate number after '#lp remove <lp>'."

        
        elif command == "list":
            lps = mongo_license_plate_find({"line": user_data['line']})
            if lps:
                reply_text = "License Plates associated with your account:\n"
                for lp in lps:
                    reply_text += f"- {lp['plate']}\n"
            else:
                reply_text = "No license plates found for your account."
        else:
            reply_text = "Invalid command. Use #lp add <plate_number>, #lp remove <plate_number>, or #lp list."
    else:
        reply_text = "User profile not found."

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

def command_liff(event):
    reply_text = "https://liff.line.me/2006527692-bk9DWq73"
    with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )