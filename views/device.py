from flask import jsonify, current_app
import json
from flask import Blueprint, request
from tencent import tencent_info
from flex import flex_set, flex_list
device = Blueprint('device', __name__)


@device.route('/<string:site_no>', methods=['GET'])
def device_index(site_no):
    # 发送GET请求到外部API
    response = flex_list(current_app)
    # 检查响应状态码
    if response.status_code == 200:
        data = response.json()
        boxes = []
        for item in data:
            if item['id'] == site_no:
                for boxReg in item['boxRegs']:
                    # connectionState 0：未知 1：已连接 2：超时 3：断开
                    box = {'alias': boxReg['alias'], 'box_no': boxReg['box']['boxNo'],
                           'connection_state': boxReg['box']['connectionState']}
                    boxes.append(box)
        # 如果请求成功，返回响应内容
        return jsonify(boxes)
    else:
        # 如果请求失败，返回错误信息
        return jsonify({'error': 'Failed to fetch data', 'status_code': response.status_code}), response.status_code


@device.route('/get/<string:box_no>', methods=['GET'])
def device_get(box_no):
    data_dict = tencent_info(box_no)
    if data_dict is None or len(data_dict) == 0:
        return jsonify('设备未创建或是已删除')
    else:
        # 更新数据库
        return {'box_no': box_no, 'data': {key: value['Value'] for key, value in data_dict.items()}}


@device.route('/set/<string:box_no>', methods=['POST'])
def device_set(box_no):
    request_data = json.loads(request.get_data())
    return jsonify(flex_set(current_app, box_no, request_data['field'], request_data['value']))
