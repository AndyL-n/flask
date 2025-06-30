from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep, time
from datetime import datetime, timezone
import requests
from db import db

# 创建后台调度器
scheduler = BackgroundScheduler()

# 获取token
def refresh_token(app):
    try:
        # 发送请求获取新的token
        response = requests.post(app.config['FBOX'] + '/idserver/core/connect/token', data={
            'scope': 'fbox',
            'client_id': '21839b55411b4aba8d6f83e6e632d5f8',
            'client_secret': '57ae529d52034486a6702adb64176e3a',
            'grant_type': 'client_credentials'
        })

        if response.status_code == 200:
            data = response.json()
            token = data.get('token_type') + " " + data.get('access_token')
            print(f"Token: {token}")
            app.config['TOKEN'] = token
            return token
        else:
            print(f"Failed to refresh token. Status code: {response.status_code}, Response: {response.text}")
    except requests.RequestException as e:
        print(f"An error occurred while refreshing token: {e}")
    return None




def device_record(app):
    with app.app_context():  # 使用传入的 app 创建上下文
        # 这里假设我们要读取所有设备信息
        from models import Device, Site
        # 从 Site 表中筛选出 delete 为 0 的记录，并获取 Site_no 列表
        sites = Site.query.filter_by(delete=0).all()
        site_no = [site.no for site in sites]
        # 使用 Site_no 列表作为条件，从 Device 表中查询相关的设备信息
        all_devices = Device.query.filter(Device.site_no.in_(site_no)).all()
        for device in all_devices:
            sleep(1000)
            print(f"Device alias: {device.alias}, Device no: {device.box_no}, Site Name: {device.site_name}")
            # 请求的URL
            url = app.config['FBOX'] + '/api/v2/dmon/value/get?boxNo=' + device.box_no

            # 请求头
            headers = {
                'Authorization': app.config['TOKEN'],  # 从应用配置中获取token
                'Content-Type': 'application/json'
            }
            # 请求体数据
            data = {
                "names": ["PM 10值", "PM2.5值", "水压备用", "A相电流", "B相电流", "C相电流", "低水位状态", "喷淋状态", "PM2.5超限", "PM10超限"],
                "timeOut": None
            }
            # 发送POST请求
            response = requests.post(url, headers=headers, json=data)
            # 检查响应状态码
            if response.status_code == 200:
                connectionState = -1
                for item in response.json():
                    if item == None and connectionState == -1:
                        connectionState = 0
                        break
                    if item == None and connectionState == 1:
                        connectionState = 2
                        break
                    connectionState = 1
                    print(device.alias, device.box_no, item['name'], item['value'], item['timestamp'])  # 打印响应的JSON数据
                    if item['name'] == 'PM 10值':
                        device.pm_10 = float(item['value'])
                    elif item['name'] == 'PM2.5值':
                        device.pm_2_5 = float(item['value'])
                    elif item['name'] == '水压备用':
                        device.water_pressure = float(item['value'])
                    elif item['name'] == 'A相电流':
                        device.phase_a = float(item['value'])
                    elif item['name'] == 'B相电流':
                        device.phase_b = float(item['value'])
                    elif item['name'] == 'C相电流':
                        device.phase_c = float(item['value'])
                    elif item['name'] == '低水位状态':
                        device.water = bool(int(item['value']))
                    elif item['name'] == '喷淋状态':
                        device.spray = bool(int(item['value']))
                    elif item['name'] == 'PM2.5超限':
                        device.pm_2_5_limit = float(item['value'])
                    elif item['name'] == 'PM10超限':
                        device.pm_10_limit = float(item['value'])



                # 将时间戳转换为datetime对象，指定时区为UTC
                dt = datetime.fromtimestamp(time(), timezone.utc)
                # 将datetime对象格式化为ISO 8601格式的字符串，包含时区信息
                iso_time_str = dt.isoformat(timespec='milliseconds') + 'Z'

                print(device.alias, device.box_no, '在线状态', connectionState, iso_time_str)
                device.connection_state = connectionState
                # 提交更改到数据库
                db.session.commit()
                #


            else:
                print(f"请求失败，状态码: {response.status_code}")
            # sleep(1)