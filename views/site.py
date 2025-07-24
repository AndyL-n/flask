from flask import jsonify, current_app
from flask import Blueprint
from mindspore.ops import switch

from models import db, Site, Union, Device, SiteRecord
from datetime import datetime
from flex import flex_list
site = Blueprint('site', __name__)


@site.route('/', methods=['GET'])
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
            new_site = Site(name=name, no=no)
            # 查询是否存在具有相同地名的工地
            existing_site = Site.query.filter_by(name=name).first()
            if existing_site:
                # 如果用户已存在
                if existing_site.no != no:
                    existing_site.no = no
                    db.session.commit()
            else:
                db.session.add(new_site)
                db.session.commit()
            flag = False
            for boxReg in item['boxRegs']:
                new_device = Device(alias=boxReg['alias'], box_no=boxReg['box']['boxNo'],
                                    connection_state=boxReg['box']['connectionState'],
                                    site_no=item['id'], site_name=item['name'], timestamp=datetime.now())
                if boxReg['box']['connectionState'] == 1:
                    flag = True
                existing_device = Device.query.filter_by(box_no=boxReg['box']['boxNo']).first()
                if existing_device:
                    existing_device.connection_state = boxReg['box']['connectionState']
                    db.session.commit()
                    continue
                else:
                    db.session.add(new_device)
                    db.session.commit()
            if flag:
                existing_site.delete = 0
                db.session.commit()

        return jsonify(data)
    else:
        # 如果请求失败，返回错误信息
        return jsonify({'error': 'Failed to fetch data', 'status_code': response.status_code}), response.status_code


@site.route('/list', methods=['GET'])
def site_list():
    sites = Site.query.filter_by(delete=0).all()
    if sites:
        sites_dict_list = [{'name': item.name, 'no': item.no} for item in sites]
        return jsonify(sites_dict_list)
    else:
        return jsonify({'message': 'Site is empty'}), 404


@site.route('/get/<string:no>', methods=['GET'])
def site_get(no):
    item = Site.query.filter(Site.no == no).first()
    if item:
        site_dict = item.to_dict()
        dt = datetime.strptime(site_dict['end_time'], '%Y-%m-%d %H:%M:%S')
        site_dict['end_time'] = dt.strftime('%Y-%m-%d')
        dt = datetime.strptime(site_dict['start_time'], '%Y-%m-%d %H:%M:%S')
        site_dict['start_time'] = dt.strftime('%Y-%m-%d')
        return jsonify(site_dict)
    else:
        return jsonify({'message': 'Site not found'}), 404


@site.route('/info/<string:no>', methods=['GET'])
def info(no):
    item = Site.query.filter(Site.no == no).first()
    if not item:
        return jsonify({'message': 'Site not found'}), 404
    site_dict = item.to_dict()
    dt = datetime.strptime(site_dict['end_time'], '%Y-%m-%d %H:%M:%S')
    site_dict['end_time'] = dt.strftime('%Y-%m-%d')
    dt = datetime.strptime(site_dict['start_time'], '%Y-%m-%d %H:%M:%S')
    site_dict['start_time'] = dt.strftime('%Y-%m-%d')

    # index(site_no) 待补全

    union = Union.query.filter_by(type='监理单位', site_no=no).first()
    if not union:
        return jsonify({'message': 'supervision is empty'}), 404
    supervision = union.to_dict()

    union = Union.query.filter_by(type='监管部门', site_no=no).first()
    if not union:
        return jsonify({'message': 'regulation is empty'}), 404
    regulation = union.to_dict()

    unions = Union.query.filter(Union.type.notin_(['监管部门', '监理单位']), Union.site_no == no).all()
    if not unions:
        return jsonify({'message': 'unions is empty'}), 404
    unions_dict_list = [union.to_dict() for union in unions]

    devices = Device.query.filter(Device.site_no == no).all()
    device_type = {'360': 0, 'p': 0, '360+p': 0}
    for item in devices:
        if item.type == '1':
            device_type['360'] += 1
        elif item.type == '2':
            device_type['p'] += 1
        else:
            device_type['360+p'] += 1
    return jsonify({'siteInfo': site_dict, 'supervision': supervision,
                    'regulation': regulation, 'companyList': unions_dict_list, 'deviceType': device_type})

@site.route('/line/<string:no>', methods=['GET'])
def line(no):
    # 1. 修正查询条件：filter中需明确字段的筛选逻辑（原代码中SiteRecord.pm10无判断条件，会被视为True）
    # 若要查询"pm10和pm2_5存在的记录"，可改为：
    records = SiteRecord.query.filter(
        SiteRecord.site_no == no,
        SiteRecord.pm10.isnot(None),  # 排除pm10为空的记录
        SiteRecord.pm2_5.isnot(None)  # 排除pm2_5为空的记录
    ).all()

    # 2. 遍历记录时，通过对象属性访问字段（而非解包）
    # 收集所有记录的pm10和pm2_5，用于返回
    pm10, pm2_5, timestamp = [], [], []
    for record in records:
        # 访问SiteRecord对象的pm10和pm2_5属性
        pm10.append(record.pm10)
        pm2_5.append(record.pm2_5)

        formatted = record.timestamp.strftime("%Y/%m/%d %H:%M").replace("/0", "/").replace(" 0", " ")
        timestamp.append(formatted)

    # 3. 返回所有记录的数据（原代码只返回最后一条，此处修正为返回全部）
    return jsonify({'pm10': pm10, 'pm2_5': pm2_5, 'timestamp': timestamp})
