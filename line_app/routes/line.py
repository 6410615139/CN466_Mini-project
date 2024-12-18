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
    PushMessageRequest,
    TextMessage,
    ImageMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

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
        if event.message.text == "#liff":
            command_liff(event)
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
        'username': display_name,
        'picture': pic_url,
        'command': user_message
    }
    # mongo_user_insert(user_data)

def exist_user(event):
    user_id = event.source.user_id
    exist = User.get_user_by_line_id(user_id)
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
    user_data = User.get_user_by_line_id(event.source.user_id).get_user_data()
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
    user = User.get_user_by_line_id(event.source.user_id)
    user_data = user.get_user_data()
    reply_text = "Invalid command. Use #lp add <plate_number>, #lp remove <plate_number>, or #lp list."  # Default reply text
    
    if user_data:
        command_parts = user_message.split(" ", 2)  # Split into at most 3 parts
        if len(command_parts) < 2:
            reply_text = "Invalid command format. Use #lp add <plate_number>, #lp remove <plate_number>, or #lp list."
        else:
            command = command_parts[1].lower()  # Normalize the command to lowercase

            if command == "add":
                if len(command_parts) == 3:
                    plate_number = command_parts[2]
                    reply_text = user.add_plate(plate_number)
                else:
                    reply_text = "Please provide a valid license plate number after '#lp add <lp>'."

            elif command == "remove":
                if len(command_parts) == 3:
                    plate_number = command_parts[2]
                    reply_text = user.remove_plate(plate_number)
                else:
                    reply_text = "Please provide a valid license plate number after '#lp remove <lp>'."

            elif command == "list":
                lps = user.find_plate()
                if lps:
                    reply_text = "License Plates associated with your account:\n"
                    reply_text += "\n".join(f"- {lp['plate']}, status: {lp['status']}" for lp in lps)
                else:
                    reply_text = "No license plates found for your account."

    else:
        reply_text = "User profile not found."

    # Send reply
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

def push_message(user_id, message):
    """
    Send a push message to a user via LINE Messaging API.

    Args:
        user_id (str): The recipient's LINE user ID.
        message (str): The message text to send.
    """
    try:
        # Configure the LINE Messaging API client
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            
            # Send the push message
            response = line_bot_api.push_message_with_http_info(
                PushMessageRequest(
                    to=user_id,
                    messages=[TextMessage(text=message)]
                )
            )
            print(f"Message sent to {user_id}: {message}, Response: {response}")
    except Exception as e:
        print(f"Error sending message to {user_id}: {e}")