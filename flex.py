import requests

# 获取token
def refresh_token(app):
    print("Refreshing token...")
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
            token = data.get('token_type') + " " + data.get('access_token')
            return token
        else:
            return(f"Failed to refresh token. Status code: {response.status_code}, Response: {response.text}")
    except requests.RequestException as e:
        return(f"An error occurred while refreshing token: {e}")
    return None

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
            return flex_list()
        else:
            return response




# 繁易获取设备信息
def flex_info(app, box_no, fields):
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
            "names": fields,
            "groupnames": ['默认'] * len(fields),
            "timeOut": None
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
            return (f"请求失败，状态码: {response.status_code}")

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
            "groupname": "默认",
            "name": field,
            "type": 0,
            "value": str(value),
        }

        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)
        # 检查响应状态码
        if response.status_code == 401:
            app.config['TOKEN'] = refresh_token(app)
            return flex_set(app, box_no, field, value)
        if response.status_code == 200:
           return ("修改成功")

        else:
            return (f"请求失败，状态码: {response.status_code}")