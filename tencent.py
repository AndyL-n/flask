import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

cred = credential.Credential(secret_id='',
                             secret_key='')
httpProfile = HttpProfile()
clientProfile = ClientProfile()


def tencent_online(box_no, min_time, max_time, limit):
    # 上下线记录
    httpProfile.endpoint = 'iotvideo.tencentcloudapi.com'
    clientProfile.httpProfile = httpProfile
    from tencentcloud.iotvideo.v20211125 import iotvideo_client, models
    client = iotvideo_client.IotvideoClient(cred, 'ap-guangzhou', clientProfile)

    req = models.DescribeDeviceStatusLogRequest()
    params = {
        'MinTime': min_time,
        'MaxTime': max_time,
        'ProductId': '7OWJE12PRR',
        'DeviceName': str(box_no),
        'Limit': limit
    }
    req.from_json_string(json.dumps(params))
    resp = client.DescribeDeviceStatusLog(req)
    # print(resp.Results)
    for time in resp.Results:
        print(time.Time, time.Type)


def tencent_info(box_no):
    # 实时信息
    try:
        from tencentcloud.iotexplorer.v20190423 import iotexplorer_client, models
        httpProfile.endpoint = 'iotexplorer.tencentcloudapi.com'
        clientProfile.httpProfile = httpProfile
        client = iotexplorer_client.IotexplorerClient(cred, 'ap-guangzhou', clientProfile)
        req = models.DescribeDeviceDataRequest()
        params = {
            'ProductId': '7OWJE12PRR',
            'DeviceName': str(box_no)
        }
        req.from_json_string(json.dumps(params))
        resp = client.DescribeDeviceData(req)
        # print(resp.Data)
        data_dict = json.loads(resp.Data)
        # print(len(data_dict))
        # for key, value in data_dict.items():
        #     print(key, value['Value'], value['LastUpdate'])
        return data_dict

    except TencentCloudSDKException as err:
        err
        return None


def tencent_record(box_no, field, min_time, max_time, limit):
    # 历史信息
    from tencentcloud.iotexplorer.v20190423 import iotexplorer_client, models
    httpProfile.endpoint = 'iotexplorer.tencentcloudapi.com'
    clientProfile.httpProfile = httpProfile
    client = iotexplorer_client.IotexplorerClient(cred, 'ap-guangzhou', clientProfile)
    req = models.DescribeDeviceDataHistoryRequest()
    params = {
        'MinTime': min_time,
        'MaxTime': max_time,
        'ProductId': '7OWJE12PRR',
        'DeviceName': str(box_no),
        'FieldName': field,
        'Limit': limit
    }
    req.from_json_string(json.dumps(params))
    resp = client.DescribeDeviceDataHistory(req)
    # print(resp.Results)
    for time in resp.Results:
        print(time.Time, time.Value)


# tencent_online(338222062369, 1752163200000, 1752422399999, 10)
tencent_info(338222062369)

# tencent_record(338222062369, 'pm10', 1752163200000, 1752422399999, 1000)
