from flask import jsonify
import json
from flask import Blueprint, request
from models import User
login = Blueprint('login', __name__)


@login.route('', methods=['POST'])
def index():
    request_data = json.loads(request.get_data())
    print('login')
    user = User.query.filter_by(name=request_data['username']).first()
    if user is None:
        return jsonify({
            'data': request_data,
            'status': 'error',
            'message': '登录失败，用户不存在'
        }), 200
    elif user.password == request_data['password']:
        return jsonify({
            'data': request_data,
            'status': 'success',
            'message': '登录成功'
        }), 200
    else:
        return jsonify({
            'data': request_data,
            'status': 'error',
            'message': '登录失败，密码错误'
        }), 200
