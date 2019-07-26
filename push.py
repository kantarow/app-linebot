from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
)
import os
import json
import random
import sys
from datetime import *
from time import *

app = Flask(__name__)
app.debug = False

line_bot_api = LineBotApi("rSGR6J4mVY3fQ8SqrCZyjtAxqT9dynuIGC87wtEGcbwLzxSGDMY2/l8YRD3cqxOcYY9JReg5uvD2kfyGGUdYp9yTWuoxgzFtyI5avM71zqwdCf4HuskTzn31LKFdAGnOsgLIt4fItpr1wOmQj5HN7wdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("d03905b4dadc5f6292597c595f3df85e")

@app.route("/get_mail", methods=['POST'])
def get_jeson():
    group_id = "C84a3f6c8f5e45507cdc2b6759bf558ac"
    mail_body = request.data.decode('utf-8')

    slice1 = mail_body.find("Ｉ２")
    slice2 = mail_body.find("----")
    mail_body = mail_body[slice1:slice2]
    print(mail_body)

    messages = TextSendMessage(text=mail_body)
    line_bot_api.push_message(group_id, messages=messages)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.type == "message":
        if (event.message.text == "Check: GroupID"):
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=event.source.group_id)
                ]
            )

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)