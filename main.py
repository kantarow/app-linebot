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

import cv2
import copy
import numpy as np
import paho.mqtt.client as mqtt

app = Flask(__name__)
app.debug = False

LINE_TOKEN = os.environ["LINE_TOKEN"]
LINE_SERIAL_KEY = os.environ["LINE_SERIAL_KEY"]
line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SERIAL_KEY)

MQTT_USERNAME = os.environ["MQTT_USERNAME"]
MQTT_PASSWORD = os.environ["MQTT_PASSWORD"]
MQTT_HOST = os.environ["MQTT_HOST"]
MQTT_PORT = os.environ["MQTT_PORT"]

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, password=MQTT_PASSWORD)
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)

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

    #画像を保存
    save_image(message_id, src_image_path)

    #保存したjpgファイルを読みこむ
    img = cv2.imread(SRC_IMAGE_PATH.format(message_id))

    #経路を取得する
    x, y = get_route(img)

    #経路データをjson形式にしてpublish
    json_content = json.dumps({'x': x.tolist(), 'y': y.tolist()})
    mqtt_client.publish("image", payload=json_content)


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

#画像から輪郭を抽出する関数
def get_contours(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, img_thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)
    contours, hierarchy = cv2.findContours(img_thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_L1)
    return contours

#輪郭の座標を正規化する関数
def get_coordinates(contours):
    cnt = contours[1][:, 0]

    x = cnt[:,0]
    y = cnt[:,1]

    x_min = np.min(x)

    y_min = np.min(y)

    x = x - x_min
    y = y - y_min

    x_max = np.max(x)
    y_max = np.max(y)

    x = x * (127 / x_max)
    y = y * (127 / y_max)

    return x, y

#画像から経路を求める関数
def get_route(img):
    contours = get_contours(img)
    x, y = get_coordinates(contours)
    coordinates = [[x, y] for x, y in zip(x, y)]
    coordinates_length = len(coordinates)
    route = []
    route.append(coordinates[0])
    while True:
        rem = [c for c in coordinates if c not in route]
        if len(rem) is not 0:
            diff = np.array(rem) - route[-1]
            squared = diff ** 2
            distance = squared[:, 0] + squared[:, 1]
            route.append(rem[np.argmin(distance)])
        else:
            break
    
    route = np.array(route)
    return route[:, 0], route[:, 1]

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
