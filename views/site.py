from flask import Blueprint, request, jsonify
import json
from models import  Site, Union, Device, Permission
from db import db # 引入 db 用于 with_entities 查询
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
@site.route('/list', methods=['GET'])
def site_list():
    try:
        # 1. 获取参数 (兼容 get_json 和 get_data)
        req_data = request.get_json(silent=True) or {}
        if not req_data:
            try:
                # 备用方案：手动解析 Body
                req_data = json.loads(request.get_data())
            except:
                pass  # 如果解析失败，req_data 依然是 {}，后面会校验

        # 2. 校验 user_id
        # 注意：这里是用 .get() 方法，避免直接 [ ] 访问导致 KeyError
        user_id = req_data.get('user_id')

        if not user_id:
            return jsonify({'code': 400, 'msg': '缺少参数: user_id'}), 400

        # 3. 数据库查询 (改回最稳妥的对象查询方式)
        # 使用 Permission.query 直接获取模型对象列表，避免 Tuple/Row 属性访问差异
        permission_records = Permission.query.filter_by(
            user_id=int(user_id),
            delete=0
        ).all()

        # 4. 构建返回列表
        sites_list = []
        for record in permission_records:
            # 确保 record 是对象，直接访问属性绝对安全
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
        # 打印详细错误到控制台，方便排查
        print(f"Error in site_list: {e}")
        return jsonify({'code': 500, 'msg': str(e)}), 500

@site.route('/info', methods=['GET'])
def site_info():
    try:
        # 1. 获取参数 (保留你原有的逻辑: 解析 Body 中的 JSON)
        # 客户端必须发送 Header: Content-Type: application/json
        req_data = request.get_json(silent=True) or {}

        # 兼容处理：如果 get_json 失败，尝试手动解析
        if not req_data:
            try:
                req_data = json.loads(request.get_data())
            except:
                return jsonify({'code': 400, 'msg': '无效的 JSON 参数'}), 400

        site_id = req_data.get('site_id')
        if not site_id:
            return jsonify({'code': 400, 'msg': '缺少参数: site_id'}), 400

        # 转为 int 防止类型错误
        site_id = int(site_id)

        # 2. 查询站点基础信息
        item = Site.query.filter_by(id=site_id, delete=0).first()
        if not item:
            return jsonify({'code': 404, 'msg': 'Site not found'}), 404

        # 使用模型最新的 to_dict (已包含 boundary 解析和时间转换)
        site_dict = item.to_dict()

        # 3. 查询关联单位 (优化：容错处理，找不到不报错，返回空字典)
        # 监理单位
        union_sup = Union.query.filter_by(type='监理单位', site_id=site_id, delete=0).first()
        supervision = union_sup.to_dict() if union_sup else {}

        # 监管部门
        union_reg = Union.query.filter_by(type='监管部门', site_id=site_id, delete=0).first()
        regulation = union_reg.to_dict() if union_reg else {}

        # 其他单位列表
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

        # 5. 返回数据
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

