from flask import g, jsonify
import requests
import json
from flask import Blueprint, request
from models import User

login = Blueprint('login', __name__)

@login.route('', methods=["POST"])
def index():
    request_data = json.loads(request.get_data())
    print("enter")
    user = User.query.filter_by(name=request_data["username"]).first()
    if (user == None):
        return jsonify({
            "data": request_data,
            "status": "error",
            "message": "登录失败，用户不存在"
        }), 200
    elif (user.password == request_data["password"]):
        try:
            # 发送POST请求
            response = requests.post('https://openapi.fbox360.com/idserver/core/connect/token', data={
                'scope': 'fbox',
                'client_id': '21839b55411b4aba8d6f83e6e632d5f8',
                'client_secret': '57ae529d52034486a6702adb64176e3a',
                'grant_type': 'client_credentials'
            })
            # 检查响应状态码
            if response.status_code == 200:
                # 打印响应内容
                data = response.json()
                g.token = data.get('token_type') + " " + data.get('access_token')
                print(g.token)
            else:
                print(f"请求失败，状态码: {response.status_code}，响应内容: {response.text}")
        except requests.RequestException as e:
            print(f"请求发生错误: {e}")
        return jsonify({
            "data": request_data,
            "status": "success",
            "message": "登录成功"
        }), 200
    else:
        return jsonify({
            "data": request_data,
            "status": "error",
            "message": "登录失败，密码错误"
        }), 200
