from flask import g, jsonify
from flask import Blueprint, request
from models import db, User
user = Blueprint('user', __name__)

@user.route('/add', methods=['POST'])
def add_user():
    data = request.get_json()
    new_user = User(name=data['name'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User added successfully!'})


@user.route('/get_user/<name>', methods=['GET'])
def get_user(name):
    user = User.query.filter_by(name=name).first()
    print(user)
    if user:
        return jsonify({'username': user.name, 'passowrd': user.password})
    else:
        return jsonify({'message': 'User not found!'}), 404


