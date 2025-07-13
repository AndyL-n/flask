from http.client import responses

from flask import jsonify, current_app
import requests
import json
from flask import Blueprint, request
from models import db, Site, Union, Device
from datetime import datetime
from flex import flex_list

site = Blueprint('site', __name__)


@site.route('/', methods=["GET"])
def index():
    response = flex_list(current_app)
    print(response)
    # 检查响应状态码
    if response.status_code == 200:
        # 如果请求成功，返回响应内容
        data = response.json()
        # 遍历字典的键值对
        for item in data:
            name = item['name']
            no = item['id']
            new_Site = Site(name=name, no=no)
            # 查询是否存在具有相同地名的工地
            existing_site = Site.query.filter_by(name=name).first()
            if existing_site:
                # 如果用户已存在
                if (existing_site.no != no):
                    existing_site.no = no
                    db.session.commit()
            else:
                db.session.add(new_Site)
                db.session.commit()
            flag = False
            for boxReg in item["boxRegs"]:
                new_device = Device(alias=boxReg["alias"], box_no=boxReg['box']['boxNo'], connection_state=boxReg['box']['connectionState'],site_no=item['id'], site_name=item['name'],timestamp=datetime.now())
                if(boxReg['box']['connectionState'] == 1):
                    flag = True
                existing_device = Device.query.filter_by(box_no=boxReg['box']['boxNo']).first()
                if existing_device:
                    existing_device.connection_state=boxReg['box']['connectionState']
                    db.session.commit()
                    continue
                else:
                    db.session.add(new_device)
                    db.session.commit()
            if(flag):
                existing_site.delete = 0
                db.session.commit()

        return jsonify(data)
    else:
        # 如果请求失败，返回错误信息
        return jsonify({'error': 'Failed to fetch data', 'status_code': response.status_code}), response.status_code


@site.route('/list', methods=["GET"])
def list():
    sites = Site.query.filter_by(delete=0).all()
    if sites:
        sites_dict_list = [{"name": site.name, "no": site.no} for site in sites]
        return jsonify(sites_dict_list)
    else:
        return jsonify({"message": "Site is empty"}), 404


@site.route('/get/<string:no>', methods=["GET"])
def get(no):
    site = Site.query.filter(Site.no == no).first()
    if site:
        site_dict = site.to_dict()
        dt = datetime.strptime(site_dict['end_time'], '%Y-%m-%d %H:%M:%S')
        site_dict['end_time'] = dt.strftime('%Y-%m-%d')
        dt = datetime.strptime(site_dict['start_time'], '%Y-%m-%d %H:%M:%S')
        site_dict['start_time'] = dt.strftime('%Y-%m-%d')
        return jsonify(site_dict)
    else:
        return jsonify({"message": "Site not found"}), 404


@site.route('/info/<string:no>', methods=["GET"])
def info(no):
    site = Site.query.filter(Site.no == no).first()
    if not site:
        return jsonify({"message": "Site not found"}), 404
    site_dict = site.to_dict()
    dt = datetime.strptime(site_dict['end_time'], '%Y-%m-%d %H:%M:%S')
    site_dict['end_time'] = dt.strftime('%Y-%m-%d')
    dt = datetime.strptime(site_dict['start_time'], '%Y-%m-%d %H:%M:%S')
    site_dict['start_time'] = dt.strftime('%Y-%m-%d')

    union = Union.query.filter_by(type='监理单位', site_no=no).first()
    if not union:
        return jsonify({"message": "supervision is empty"}), 404
    supervision = union.to_dict()

    union = Union.query.filter_by(type='监管部门', site_no=no).first()
    if not union:
        return jsonify({"message": "regulation is empty"}), 404
    regulation = union.to_dict()

    unions = Union.query.filter(Union.type.notin_(['监管部门', '监理单位']), Union.site_no == no).all()
    if not unions:
        return jsonify({"message": "unions is empty"}), 404
    unions_dict_list = [union.to_dict() for union in unions]
    return jsonify({'siteInfo': site_dict, 'supervision': supervision, 'regulation':regulation, 'companyList':unions_dict_list})
