import requests


# 获取token
def refresh_token(app):
    print('Refreshing token...')
    try:
        # 发送请求获取新的token
        response = requests.post(app.config['FBOX'] + '/idserver/core/connect/token', data={
            'scope': 'fbox',
            'client_id': '6e8fee657be743a5bd0f8aea5f1339d1',
            'client_secret': '608a6d20640c4a6ea21fbbd661649afa',
            'grant_type': 'client_credentials'
        })

        if response.status_code == 200:
            data = response.json()
            token = data.get('token_type') + ' ' + data.get('access_token')
            return token
        else:
            return f'Failed to refresh token. Status code: {response.status_code}, Response: {response.text}'
    except requests.RequestException as e:
        return f'An error occurred while refreshing token: {e}'


# 繁易获取监控设备
def flex_list(app):
    with app.app_context():  # 使用传入的 app 创建上下文
        # 请求的URL
        url = app.config['FBOX'] + '/api/client/box/grouped'

        # 请求头
        headers = {
            'Authorization': app.config['TOKEN'],  # 从应用配置中获取token
            'Content-Type': 'application/json'
        }

        # 发送POST请求
        response = requests.get(url, headers=headers)
        # 检查响应状态码
        if response.status_code == 401:
            app.config['TOKEN'] = refresh_token(app)
            return flex_list(app)
        else:
            return response


# 繁易获取设备信息
def flex_info(app, box_no, fields=[
    "PM2.5值",
    "PM 10值",
    "水压备用",
    "A相电流",
    "B相电流",
    "C相电流",
    "低水位状态",
    "喷淋状态",
    "模式选择",
    "远程开关",
    "报警复位",
    "暂停时长",
    "喷淋时长",
    "缺水复位",
    "PM2.5超限",
    "PM10超限",
    "电流上限设置",
    "电流下限设置",
    "周一启用",
    "周二启用",
    "周三启用",
    "周四启用",
    "周五启用",
    "周六启用",
    "周日启用",
    "01时段启用选择",
    "01时段开启时",
    "01时段开启分",
    "01时段关闭时",
    "01时段关闭分",
    "02时段启用选择",
    "02时段开启时",
    "02时段开启分",
    "02时段关闭时",
    "02时段关闭分",
    "03时段启用选择",
    "03时段开启时",
    "03时段开启分",
    "03时段关闭时",
    "03时段关闭分",
    "04时段启用选择",
    "04时段开启时",
    "04时段开启分",
    "04时段关闭时",
    "04时段关闭分",
    "05时段启用选择",
    "05时段开启时",
    "05时段开启分",
    "05时段关闭时",
    "05时段关闭分",
    "06时段启用选择",
    "06时段开启时",
    "06时段开启分",
    "06时段关闭时",
    "06时段关闭分",
    "显示-年",
    "显示-月",
    "显示-日",
    "显示-时",
    "显示-分",
    "显示-秒",
    "显示-周",
    "设置-年",
    "设置-月",
    "设置-日",
    "设置-时",
    "设置-分",
    "设置-秒",
    "设置-周",
    "确认修改时钟",
    "1#喷头启用",
    "2#喷头启用",
    "1#喷头手自动",
    "2#喷头手自动",
    "1#当前角度",
    "2#当前角度",
    "1#喷头设置角度",
    "2#喷头设置角度",
    "1#喷头水阀启动",
    "2#喷头水阀启动",
    "1#喷头手动正转",
    "1#喷头手动反转",
    "2#喷头手动正转",
    "2#喷头手动反转",
    "1#喷头单圈脉冲",
    "2#喷头单圈脉冲",
    "手动旋转喷头速度",
    "自动旋转喷头速度"
]):
    with app.app_context():  # 使用传入的 app 创建上下文
        # 请求的URL
        url = app.config['FBOX'] + '/api/v2/dmon/value/get?boxNo=' + str(box_no)

        # 请求头
        headers = {
            'Authorization': app.config['TOKEN'],  # 从应用配置中获取token
            'Content-Type': 'application/json'
        }

        # 请求体数据
        data = {
            'names': fields,
            'groupnames': ['默认'] * len(fields),
            'timeOut': None
        }

        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)
        # 检查响应状态码

        if response.status_code == 401:
            app.config['TOKEN'] = refresh_token(app)
            return flex_info(app, box_no, fields)
        elif response.status_code == 200:
            return response.json()
        else:
            return f'请求失败，状态码: {response.status_code}'


# 繁易修改设备信息
def flex_set(app, box_no, field, value):
    with app.app_context():  # 使用传入的 app 创建上下文
        # 请求的URL
        url = app.config['FBOX'] + '/api/v2/dmon/value?boxNo=' + str(box_no)

        # 请求头
        headers = {
            'Authorization': app.config['TOKEN'],  # 从应用配置中获取token
            'Content-Type': 'application/json'
        }

        # 请求体数据
        data = {
            'groupname': '默认',
            'name': field,
            'type': 0,
            'value': str(value),
        }

        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)
        # 检查响应状态码
        if response.status_code == 401:
            app.config['TOKEN'] = refresh_token(app)
            return flex_set(app, box_no, field, value)
        if response.status_code == 200:
            return '修改成功'

        else:
            return f'请求失败，状态码: {response.status_code}'
