from flask import g, jsonify
import requests
import json
from flask import Blueprint, request
from models import db, Union

union = Blueprint('union', __name__)

@union.route('/list/<string:site_no>', methods=["GET"])
def list(site_no):
    unions = Union.query.filter(Union.type.notin_(['监管部门', '监理单位']), Union.site_no == site_no).all()
    if unions:
        unions_dict_list = [union.to_dict() for union in unions]
        return jsonify(unions_dict_list), 200

    else:
        return jsonify({"message": "Site is empty"}), 404

# 监理单位
@union.route('/get_supervision/<string:site_no>', methods=["GET"])
def getSupervision(site_no):
    union = Union.query.filter_by(type='监理单位', site_no=site_no).first()
    if union:
        return jsonify(union.to_dict()), 200
    else:
        return jsonify({"message": "Site is empty"}), 404

# 监管部门
@union.route('/get_regulation/<string:site_no>', methods=["GET"])
def getRegulation(site_no):
    union = Union.query.filter_by(type='监管部门', site_no=site_no).first()
    if union:
        return jsonify(union.to_dict()), 200
    else:
        return jsonify({"message": "Site is empty"}), 404
