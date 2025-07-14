from flask import jsonify
from flask import Blueprint
from models import Union
union = Blueprint('union', __name__)


@union.route('/list/<string:site_no>', methods=["GET"])
def union_list(site_no):
    unions = Union.query.filter(Union.type.notin_(['监管部门', '监理单位']), Union.site_no == site_no).all()
    if unions:
        unions_dict_list = [item.to_dict() for item in unions]
        return jsonify(unions_dict_list), 200

    else:
        return jsonify({"message": "Site is empty"}), 404


# 监理单位
@union.route('/get_supervision/<string:site_no>', methods=["GET"])
def get_supervision(site_no):
    item = Union.query.filter_by(type='监理单位', site_no=site_no).first()
    if item:
        return jsonify(item.to_dict()), 200
    else:
        return jsonify({"message": "Site is empty"}), 404


# 监管部门
@union.route('/get_regulation/<string:site_no>', methods=["GET"])
def get_regulation(site_no):
    item = Union.query.filter_by(type='监管部门', site_no=site_no).first()
    if item:
        return jsonify(item.to_dict()), 200
    else:
        return jsonify({"message": "Site is empty"}), 404
