from flask import Blueprint, request, jsonify
import json
from models import  Site, Union, Device, SiteRecord, Permission
from datetime import datetime

# 通用函数：兼容 T 分隔和空格分隔的时间字符串
def parse_time_to_date(time_str):
    # 步骤1：将字符串中的 T 替换为空格（统一格式）
    time_str_clean = time_str.replace('T', ' ')
    # 步骤2：用空格格式解析（此时已无T，可正常解析）
    dt = datetime.strptime(time_str_clean, '%Y-%m-%d %H:%M:%S')
    # 步骤3：返回只保留日期的格式
    return dt.strftime('%Y-%m-%d')

site = Blueprint('site', __name__)


@site.route('/', methods=['GET'])
def index():
    return "site"

@site.route('/list', methods=['GET'])
def site_list():
    try:
        request_data = json.loads(request.get_data())
        user_id = int(request_data['user_id'])
        permission_records = Permission.query.filter_by(delete=0, user_id=user_id).all()
        sites_dict_list = []
        for record in permission_records:
            sites_dict_list.append({
                "site_id": record.site_id,  # 直接获取Permission表的site_id字段
                "site_name": record.site_name  # 直接获取Permission表的site_name字段
            })
        return jsonify(sites_dict_list)
    except Exception as e:
        return jsonify({"msg": str(e)})

@site.route('/info', methods=['GET'])
def site_info():
    try:
        request_data = json.loads(request.get_data())
        site_id = int(request_data['site_id'])
        item = Site.query.filter_by(id=site_id, delete=0).first()
        if not item:
            return jsonify({'message': 'Site not found'}), 404
        site_dict = item.to_dict()
        site_dict['end_time'] = parse_time_to_date(site_dict['end_time'])
        site_dict['start_time'] = parse_time_to_date(site_dict['start_time'])

        union = Union.query.filter_by(type='监理单位', site_id=site_id, delete=0).first()
        if not union:
            return jsonify({'message': 'supervision is empty'}), 404
        supervision = union.to_dict()

        union = Union.query.filter_by(type='监管部门', site_id=site_id, delete=0).first()
        if not union:
            return jsonify({'message': 'regulation is empty'}), 404
        regulation = union.to_dict()

        unions = Union.query.filter(Union.type.notin_(['监管部门', '监理单位']), Union.site_id == site_id, Union.delete == 0).all()
        if not unions:
            return jsonify({'message': 'unions is empty'}), 404
        unions_dict_list = [union.to_dict() for union in unions]

        devices = Device.query.filter(Device.site_id == site_id).all()
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

    except Exception as e:
        return jsonify({"msg": str(e)})

# 查看所有GPS
@site.route('/gps', methods=['GET'])
def site_gps():
    try:
        # 1. 获取参数 (沿用你项目现有的风格: GET请求中解析Body)
        # 注意：标准RESTful开发中建议GET请求使用 request.args.get('site_id')
        request_data = json.loads(request.get_data())
        site_id = int(request_data['site_id'])

        # 2. 查询该站点下所有未删除的设备
        devices = Device.query.filter_by(site_id=site_id, delete=0).all()
        print(devices)
        gps_list = []
        for device in devices:
            print(device.longitude)
            # 3. 构建返回数据
            # 注意：数据库中的 Decimal 类型需要转为 float，否则 JSON 序列化会报错
            gps_data = {
                "device_name": device.device_name,
                "alias": device.alias,  # 设备别名，地图打点显示用
                "status": device.status, # 在线状态 (1在线/0离线)，前端可据此显示不同颜色图标
                "longitude": float(device.longitude) if device.longitude is not None else None,
                "latitude": float(device.latitude) if device.latitude is not None else None
            }
            print(gps_data)
            gps_list.append(gps_data)

        # 4. 返回 JSON 列表
        return jsonify({
            "code": 200,
            "msg": "success",
            "data": gps_list
        })

    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})

# 获取record_list

