from flask import jsonify
from flask import Blueprint, request
from models import db, User

user = Blueprint('user', __name__)


@user.route('/add', methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(name=data['name'], password=data['password'])
    # 查询是否存在具有相同地名的工地
    existing_user = User.query.filter_by(name=data['name']).first()
    if existing_user:
        return jsonify({'error': 'User already exists'})
    else:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User added successfully!'})


@user.route('/get_user/<name>', methods=['GET'])
def get_user(name):
    item = User.query.filter_by(name=name).first()
    print(item)
    if item:
        return jsonify({'username': item.name, 'password': item.password})
    else:
        return jsonify({'message': 'User not found!'}), 404
