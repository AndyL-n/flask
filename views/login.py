from flask import Blueprint, request, jsonify
import json
from models import User

login = Blueprint('login', __name__)


# 建议增加 POST 支持，因为 GET 请求带密码不安全
@login.route('', methods=['GET', 'POST'])
def index():
    try:
        # ==========================================
        # 1. 参数获取逻辑 (兼容 URL 参数 和 Body JSON)
        # ==========================================
        username = None
        password = None
        request_data = {}  # 用于返回给前端回显

        # 方式 A: 优先尝试从 URL (Query String) 获取
        # 例如: /login?username=admin&password=123
        if request.args.get('username'):
            username = request.args.get('username')
            password = request.args.get('password')
            request_data = request.args.to_dict()

        # 方式 B: 如果 URL 没传，尝试从 Body JSON 获取
        # 兼容 curl 和 axios data
        if not username:
            # get_json(silent=True) 不会报错，解析失败返回 None
            json_data = request.get_json(silent=True)

            # 如果 get_json 没拿到，尝试手动解析 raw data (针对某些特殊客户端)
            if json_data is None and request.get_data():
                try:
                    json_data = json.loads(request.get_data())
                except:
                    pass

            if json_data:
                username = json_data.get('username')
                password = json_data.get('password')
                request_data = json_data

        # ==========================================
        # 2. 参数校验
        # ==========================================
        if not username or not password:
            return jsonify({
                'data': request_data,
                'status': 'error',
                'message': '登录失败，缺少用户名或密码'
            }), 200  # 或者是 400，保持你原有的 200

        # ==========================================
        # 3. 业务逻辑 (查询用户)
        # ==========================================
        user = User.query.filter_by(name=username).first()

        if user is None:
            return jsonify({
                'data': request_data,
                'status': 'error',
                'message': '登录失败，用户不存在'
            }), 200

        elif user.password == password:
            return jsonify({
                'data': {
                    "name": user.name,
                    "site_id": user.site_id,
                    # 如果有 token 生成逻辑通常放在这里
                    # "token": "xxxxx"
                },
                'status': 'success',
                'message': '登录成功'
            }), 200

        else:
            return jsonify({
                'data': request_data,
                'status': 'error',
                'message': '登录失败，密码错误'
            }), 200

    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'服务器内部错误: {str(e)}'
        }), 500