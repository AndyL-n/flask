import json
import logging
import os
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
# 导入两个不同的 SDK 包
from tencentcloud.iotexplorer.v20190423 import iotexplorer_client, models as explorer_models
from tencentcloud.iotvideo.v20201215 import iotvideo_client, models as video_models
from config import Config

# 1. 强制禁用系统代理
os.environ['NO_PROXY'] = '*'
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TencentIoT")


class TencentIoTHandler:
    def __init__(self):
        """初始化腾讯云客户端连接 (双 Client 模式)"""
        try:
            self.product_id = Config.TENCENT_PRODUCT_ID
            self.secret_id = Config.TENCENT_SECRET_ID
            self.secret_key = Config.TENCENT_SECRET_KEY

            if not all([self.product_id, self.secret_id, self.secret_key]):
                logger.error("Tencent Cloud config missing! Check .env file.")
                raise ValueError("Missing Tencent Cloud Configuration")

            # 共用凭证
            self.cred = credential.Credential(self.secret_id, self.secret_key)

            # ==========================================
            # 1. 初始化 Explorer Client (用于读取数据)
            # ==========================================
            httpProfile_exp = HttpProfile()
            httpProfile_exp.endpoint = "iotexplorer.tencentcloudapi.com"

            clientProfile_exp = ClientProfile()
            clientProfile_exp.httpProfile = httpProfile_exp

            self.explorer_client = iotexplorer_client.IotexplorerClient(self.cred, "ap-guangzhou", clientProfile_exp)

            # ==========================================
            # 2. 初始化 Video Client (用于控制设备 - 还原源代码逻辑)
            # ==========================================
            httpProfile_vid = HttpProfile()
            httpProfile_vid.endpoint = "iotvideo.tencentcloudapi.com"

            clientProfile_vid = ClientProfile()
            clientProfile_vid.httpProfile = httpProfile_vid

            # 原代码中 region 为空字符串 ""，这里建议使用 "ap-guangzhou" 或与原代码保持一致
            # 为了保险起见，这里设置为 "ap-guangzhou"，如果报错请尝试改回 ""
            self.video_client = iotvideo_client.IotvideoClient(self.cred, "ap-guangzhou", clientProfile_vid)

            logger.info("Tencent IoT Clients (Explorer & Video) Initialized.")

        except Exception as e:
            logger.error(f"Init Failed: {str(e)}")

    def get_device_data(self, device_name):
        """获取设备最新数据 (使用 Explorer SDK)"""
        try:
            # 1. 获取在线状态
            req_status = explorer_models.DescribeDeviceRequest()
            params_status = {
                "ProductId": self.product_id,
                "DeviceName": str(device_name),
            }
            req_status.from_json_string(json.dumps(params_status))
            resp_status = self.explorer_client.DescribeDevice(req_status)

            result = {'status': resp_status.Device.Status}  # 1: 在线, 0: 离线

            # 2. 获取属性数据
            req_data = explorer_models.DescribeDeviceDataRequest()
            params_data = {
                'ProductId': self.product_id,
                'DeviceName': str(device_name)
            }
            req_data.from_json_string(json.dumps(params_data))
            resp_data = self.explorer_client.DescribeDeviceData(req_data)

            if hasattr(resp_data, 'Data'):
                data_dict = json.loads(resp_data.Data)
                for key, value in data_dict.items():
                    if 'Value' in value:
                        result[key] = value['Value']

            return result

        except TencentCloudSDKException as err:
            logger.error(f"Get Data Error [{device_name}]: {err}")
            return None
        except Exception as e:
            logger.error(f"Unknown Error [{device_name}]: {e}")
            return None

    def control_device(self, device_name, data_dict):
        """
        下发控制指令 (使用 Video SDK - 还原源代码逻辑)
        :param device_name: 设备名称
        :param data_dict: 要修改的属性字典
        """
        try:
            if not data_dict:
                return False

            # 注意：这里使用 video_models (iotvideo SDK)
            req = video_models.ControlDeviceDataRequest()

            params = {
                "ProductId": self.product_id,
                "DeviceName": str(device_name),
                "Data": json.dumps(data_dict)  # 必须序列化为字符串
            }
            req.from_json_string(json.dumps(params))

            # 使用 video_client 发送请求
            resp = self.video_client.ControlDeviceData(req)

            logger.info(f"Control Device [{device_name}] Success. Resp: {resp.to_json_string()}")
            return True

        except TencentCloudSDKException as err:
            logger.error(f"Control Device Error [{device_name}]: {err}")
            return False
        except Exception as e:
            logger.error(f"Control Unknown Error [{device_name}]: {e}")
            return False


# 单例模式
tencent_handler = TencentIoTHandler()