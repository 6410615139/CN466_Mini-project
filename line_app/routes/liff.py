# line_routes.py
from flask import Blueprint, request, jsonify, render_template, abort
from utils.sqlite import dbase_query, update_last_record
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import os

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
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# Create the 'line' blueprint
liff_blueprint = Blueprint('liff', __name__)

configuration = Configuration(access_token=os.environ['CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])

@liff_blueprint.route("/", methods=["GET"])
def liff():
    viewModel = {
        "liff_id" : os.environ['LIFF_ID'],
        "db" : dbase_query(limit=5)
    }
    return render_template('liff.html', viewModel=viewModel)

# API route to get the latest record
@liff_blueprint.route("/get_last", methods=["GET"])
def get_last():
    row = dbase_query(limit=1)[0]
    if row:
        return jsonify({"tstamp": row[1], "value": row[2]})
    else:
        return jsonify({"error": "No data available"}), 404

# API route to update the last value
@liff_blueprint.route("/update_last", methods=["PUT"])
def update_last():
    data = request.get_json()
    value = data.get("value")
    
    if value:
        update_last_record(value)
        return jsonify({"message": "Last record updated successfully"})
    else:
        return jsonify({"error": "No value provided"}), 400

@liff_blueprint.route("/callback", methods=['POST'])
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
    if event.message.text == "notify":
        reply = dbase_query(limit=5)
    else:
        reply = event.message.text

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=str(reply))]
            )
        )
