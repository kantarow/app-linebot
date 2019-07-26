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
import requests
from pathlib import Path

app = Flask(__name__)
app.debug = False

line_bot_api = LineBotApi("g8MgkA0jNHdSRUA9ZqCyuNEgmhsO9/dhMhkQQcx9+IlRFi0IdGuD91tNbYlxWnMJC+2ykuNH/eZRuV/mGGoy7iTtjAiunkdQM2HcGo6spKxm9SExVwdpqLJeeTU8GtKixaUOFHJrfvfNkAvvr539ZwdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("9deb0d85b6c78853f031b3240a6e64c5")

#送信先から取得した画像のPATH
SRC_IMAGE_PATH = "{}.jpg"

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
    #テスト用。CheckIDと送るとそのユーザーのユーザーIDが送り返される。
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

    #保存する画像のPATH, POSTする画像のPATHを生成
    src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()
    post_image_path = SRC_IMAGE_PATH.format(message_id)

    #画像を保存&POST
    save_image(message_id, src_image_path)
    post_image(post_image_path)

    #正常に進んだら最終的にユーザーにOKと送信
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="OK"))

    #POSTしたら保存された画像は不要なので削除する
    src_image_path.unlink()

def save_image(message_id: str, save_path: str) -> None:
    #画像のバイナリデータを取得
    message_content = line_bot_api.get_message_content(message_id)

    #バイナリを1024バイトずつ書き込む
    with open(save_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

def post_image(post_path):
    files = {'file': open(post_path, 'rb')}
    #画像処理サーバのURLに変更すれば完成
    r = requests.post('http://', files=files)

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)