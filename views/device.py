from flask import g, jsonify, current_app
import requests
import json
from flask import Blueprint, request
from models import Device
from flex import device_set, device_list

device = Blueprint('device', __name__)

@device.route('/<string:site_no>', methods=["GET"])
def index(site_no):
    # 发送GET请求到外部API
    response = device_list(current_app)
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

@device.route('/set/<string:box_no>', methods=["GET"])
def set(box_no):
    request_data = json.loads(request.get_data())
    return jsonify(device_set(current_app, box_no, request_data["name"], request_data["value"]))

import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile


# from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# try:
#     print("enter")
# except TencentCloudSDKException as err:
#     print(err)

cred = credential.Credential()
httpProfile = HttpProfile()
httpProfile.endpoint = "iotvideo.tencentcloudapi.com"
clientProfile = ClientProfile()
clientProfile.httpProfile = httpProfile

# 上下线记录
from tencentcloud.iotvideo.v20211125 import iotvideo_client, models
client = iotvideo_client.IotvideoClient(cred, "ap-guangzhou", clientProfile)

req = models.DescribeDeviceStatusLogRequest()
params = {
    "MinTime": 1752163200000,
    "MaxTime": 1752422399999,
    "ProductId": "7OWJE12PRR",
    "DeviceName": "338222062369",
    "Limit": 10
}
req.from_json_string(json.dumps(params))
resp = client.DescribeDeviceStatusLog(req)
print(resp.to_json_string())


# 实时信息
from tencentcloud.iotexplorer.v20190423 import iotexplorer_client, models
httpProfile = HttpProfile()
httpProfile.endpoint = "iotexplorer.tencentcloudapi.com"
clientProfile = ClientProfile()
clientProfile.httpProfile = httpProfile
client = iotexplorer_client.IotexplorerClient(cred, "ap-guangzhou", clientProfile)
req = models.DescribeDeviceDataRequest()
params = {
    "ProductId": "7OWJE12PRR",
    "DeviceName": "338222062369"
}
req.from_json_string(json.dumps(params))
resp = client.DescribeDeviceData(req)
print(resp.to_json_string())


############

# 历史信息
from tencentcloud.iotexplorer.v20190423 import iotexplorer_client, models
httpProfile = HttpProfile()
httpProfile.endpoint = "iotexplorer.tencentcloudapi.com"
clientProfile = ClientProfile()
clientProfile.httpProfile = httpProfile
client = iotexplorer_client.IotexplorerClient(cred, "ap-guangzhou", clientProfile)
req = models.DescribeDeviceDataHistoryRequest()
params = {
    "MinTime": 1752404870000,
    "MaxTime": 1752404876852,
    "ProductId": "7OWJE12PRR",
    "DeviceName": "338222062369",
    "FieldName": "pm2_5",
    "Limit": 10
}
req.from_json_string(json.dumps(params))
resp = client.DescribeDeviceDataHistory(req)
print(resp.to_json_string())

