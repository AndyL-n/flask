from flask import g, jsonify, current_app
import requests
import json
from flask import Blueprint, request
from models import Device
from flex import flex_set, flex_list

device = Blueprint('device', __name__)

@device.route('/<string:site_no>', methods=["GET"])
def index(site_no):
    # 发送GET请求到外部API
    response = flex_list(current_app)
    # 检查响应状态码
    if response.status_code == 200:
        data = response.json()
        boxes = []
        for item in data:
            if(item['id'] == site_no):
                for boxReg in item["boxRegs"]:
                    # print(boxReg['alias'], boxReg['box']['boxNo'], boxReg['box']['connectionState'], item['id'], item['name'],)
                    # connectionState 0：未知 1：已连接 2：超时 3：断开
                    box = {'alias':boxReg['alias'], 'boxNo':boxReg['box']['boxNo'], 'connectionState':boxReg['box']['connectionState']}
                    boxes.append(box)
        # 如果请求成功，返回响应内容
        return jsonify(boxes)
    else:
        # 如果请求失败，返回错误信息
        return jsonify({'error': 'Failed to fetch data', 'status_code': response.status_code}), response.status_code

@device.route('/set/<string:box_no>', methods=["POST"])
def set(box_no):
    request_data = json.loads(request.get_data())
    return jsonify(flex_set(current_app, box_no, request_data["field"], request_data["value"]))

