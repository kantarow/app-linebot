from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, ImageMessage
)
import os
import json
from pathlib import Path

app = Flask(__name__)
app.debug = False

line_bot_api = LineBotApi("g8MgkA0jNHdSRUA9ZqCyuNEgmhsO9/dhMhkQQcx9+IlRFi0IdGuD91tNbYlxWnMJC+2ykuNH/eZRuV/mGGoy7iTtjAiunkdQM2HcGo6spKxm9SExVwdpqLJeeTU8GtKixaUOFHJrfvfNkAvvr539ZwdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("9deb0d85b6c78853f031b3240a6e64c5")

SRC_IMAGE_PATH = "images/{}.jpg"
MAIN_IMAGE_PATH = "images/{}_main.jpg"
PREVIEW_IMAGE_PATH = "images/{}_preview.jpg"

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
        if (event.message.text == "CheckID"):
            line_bot_api.reply_message(
                event.reply_token,
                [
                    TextSendMessage(text=event.source.user_id)
                ]
            )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    #contents = line_bot_api.get_message_content(event.message.id)

    src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()
    #main_image_path = MAIN_IMAGE_PATH.format(message_id)
    #preview_image_path = PREVIEW_IMAGE_PATH.format(message_id)
    send_image_path = SRC_IMAGE_PATH.format(message_id)

    save_image(message_id, src_image_path)

    image_message = ImageSendMessage(
        original_content_url=f"https://selfmaid.herokuapp.com/{send_image_path}",
        preview_image_url=f"https://selfmaid.herokuapp.com/{send_image_path}"
    )
    line_bot_api.reply_message(event.reply_token, image_message)

    src_image_path.unlink()

def save_image(message_id: str, save_path: str) -> None:
    message_content = line_bot_api.get_message_content(message_id)
    with open(save_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)