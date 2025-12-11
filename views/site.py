from flask import Blueprint, request, jsonify
import json
from models import Site, Union, Device, Permission
from db import db
from datetime import datetime


# 通用函数
def parse_time_to_date(time_str):
    time_str_clean = time_str.replace('T', ' ')
    dt = datetime.strptime(time_str_clean, '%Y-%m-%d %H:%M:%S')
    return dt.strftime('%Y-%m-%d')

site = Blueprint('site', __name__)


@site.route('/', methods=['GET'])
def index():
    return "site"


# ==============================================================================
# 1. 获取站点列表
# ==============================================================================
@site.route('/list', methods=['GET'])
def site_list():
    try:
        # --- 修改开始：兼容 URL 参数和 Body JSON ---
        user_id = None

        # 1. 优先尝试从 URL Query String 获取 (例如: /site/list?user_id=1001)
        if request.args.get('user_id'):
            user_id = request.args.get('user_id')

        # 2. 如果 URL 没传，再尝试从 Body JSON 获取 (兼容旧代码/Curl)
        if not user_id:
            req_data = request.get_json(silent=True) or {}
            if not req_data and request.get_data():
                try:
                    req_data = json.loads(request.get_data())
                except:
                    pass
            user_id = req_data.get('user_id')
        # --- 修改结束 ---

        if not user_id:
            return jsonify({'code': 400, 'msg': '缺少参数: user_id'}), 400

        # 3. 数据库查询
        permission_records = Permission.query.filter_by(
            user_id=int(user_id),
            delete=0
        ).all()

        # 4. 构建返回列表
        sites_list = []
        for record in permission_records:
            sites_list.append({
                "site_id": record.site_id,
                "site_name": record.site_name
            })

        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': sites_list
        })

    except Exception as e:
        print(f"Error in site_list: {e}")
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ==============================================================================
# 2. 获取站点详情
# ==============================================================================
@site.route('/info', methods=['GET'])
def site_info():
    try:
        # --- 修改开始：兼容 URL 参数和 Body JSON ---
        site_id = None

        # 1. 优先尝试从 URL Query String 获取
        if request.args.get('site_id'):
            site_id = request.args.get('site_id')

        # 2. 如果 URL 没传，尝试从 Body 获取
        if not site_id:
            req_data = request.get_json(silent=True) or {}
            if not req_data and request.get_data():
                try:
                    req_data = json.loads(request.get_data())
                except:
                    pass  # Body 解析失败忽略，后面会统一判空
            site_id = req_data.get('site_id')
        # --- 修改结束 ---

        if not site_id:
            return jsonify({'code': 400, 'msg': '缺少参数: site_id'}), 400

        site_id = int(site_id)

        # 2. 查询站点基础信息
        item = Site.query.filter_by(id=site_id, delete=0).first()
        if not item:
            return jsonify({'code': 404, 'msg': 'Site not found'}), 404

        site_dict = item.to_dict()

        # 3. 查询关联单位
        union_sup = Union.query.filter_by(type='监理单位', site_id=site_id, delete=0).first()
        supervision = union_sup.to_dict() if union_sup else {}

        union_reg = Union.query.filter_by(type='监管部门', site_id=site_id, delete=0).first()
        regulation = union_reg.to_dict() if union_reg else {}

        unions = Union.query.filter(
            Union.type.notin_(['监管部门', '监理单位']),
            Union.site_id == site_id,
            Union.delete == 0
        ).all()
        unions_dict_list = [u.to_dict() for u in unions] if unions else []

        # 4. 统计设备类型
        devices = Device.query.filter_by(site_id=site_id).all()
        device_type = {'360': 0, 'p': 0, '360+p': 0}

        for d in devices:
            d_type = str(d.type) if d.type else '0'
            if d_type == '1':
                device_type['360'] += 1
            elif d_type == '2':
                device_type['p'] += 1
            else:
                device_type['360+p'] += 1

        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'siteInfo': site_dict,
                'supervision': supervision,
                'regulation': regulation,
                'companyList': unions_dict_list,
                'deviceType': device_type
            }
        })

    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ==============================================================================
# 3. 查看所有GPS
# ==============================================================================
@site.route('/gps', methods=['GET'])
def site_gps():
    try:
        # --- 修改开始：兼容 URL 参数和 Body JSON ---
        site_id = None

        # 1. 优先 URL
        if request.args.get('site_id'):
            site_id = request.args.get('site_id')

        # 2. 其次 Body (增加了 Try-Except 保护，防止 request.get_data() 为空时报错)
        if not site_id:
            try:
                raw_data = request.get_data()
                if raw_data:
                    request_data = json.loads(raw_data)
                    site_id = request_data.get('site_id')
            except Exception as e:
                print(f"Body parse error: {e}")
        # --- 修改结束 ---

        if not site_id:
            return jsonify({'code': 400, 'msg': '缺少参数: site_id'}), 400

        site_id = int(site_id)

        # 2. 查询该站点下所有未删除的设备
        devices = Device.query.filter_by(site_id=site_id, delete=0).all()
        # print(devices) # 调试用，生产环境可注释

        gps_list = []
        for device in devices:
            # 3. 构建返回数据
            gps_data = {
                "device_name": device.device_name,
                "alias": device.alias,
                "status": device.status,
                "horizontal_angle": device.horizontal_angle,
                "longitude": float(device.longitude) if device.longitude is not None else None,
                "latitude": float(device.latitude) if device.latitude is not None else None
            }
            gps_list.append(gps_data)

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": gps_list
        })

    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500