from datetime import datetime
from flask import jsonify, current_app
import json
import pytz
from flask import Blueprint, request
from tencent import tencent_info
from flex import flex_set, flex_list
from db import db
from models import DeviceRecord, Device
# from flex import flex_info

# 定义东八区时区
tz = pytz.timezone('Asia/Shanghai')
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
    # return flex_info(current_app, box_no)
    data_dict = tencent_info(box_no)
    if data_dict is None or len(data_dict) == 0:
        return jsonify('设备未创建或是已删除')
    else:
        existing_device = Device.query.filter_by(box_no=box_no).first()
        existing_device.timestamp = datetime.now()
        info = {'type': existing_device.type,
                'site_no': existing_device.site_no,
                'site_name': existing_device.site_name,
                'connection_state': existing_device.connection_state,
                'timestamp': existing_device.timestamp
                }
        db.session.commit()
        # 更新数据库
        new_device = Record(box_no=box_no)
        clean_data = {key: value['Value'] for key, value in data_dict.items()}
        # 批量更新属性
        new_device.__dict__.update(clean_data)
        db.session.add(new_device)
        db.session.commit()
        return {'box_no': box_no, 'info': info, 'data': {key: value['Value'] for key, value in data_dict.items()}}


@device.route('/set/<string:box_no>', methods=['POST'])
def device_set(box_no):
    request_data = json.loads(request.get_data())
    return jsonify(flex_set(current_app, box_no, request_data['field'], request_data['value']))
