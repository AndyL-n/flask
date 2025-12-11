from flask import Blueprint, request, jsonify
import json
from models import Device, DeviceRecord
from db import db
from tencent import tencent_handler
from datetime import datetime  # 1. 新增引入 datetime

# 定义蓝图
device = Blueprint('device', __name__)


# ==============================================================================
# 1. 获取设备实时详情 (修改：优先从腾讯云同步最新数据)
# ==============================================================================
@device.route('/info', methods=['GET'])
def device_info():
    try:
        # --- 兼容 URL 参数和 Body JSON (保持原逻辑) ---
        device_name = None

        # 优先从 URL 参数获取
        if request.args.get('device_name'):
            device_name = request.args.get('device_name')

        # 其次从 Body 获取
        if not device_name:
            req_data = request.get_json(silent=True) or {}
            # 备用：如果 Content-Type 不对导致 get_json 失败，尝试手动解析
            if not req_data and request.get_data():
                try:
                    req_data = json.loads(request.get_data())
                except:
                    pass
            device_name = req_data.get('device_name')
        # -------------------------------------------

        if not device_name:
            return jsonify({'code': 400, 'msg': '缺少参数: device_name'}), 400

        # 1. 先查询本地数据库，确保设备存在
        device_obj = Device.query.filter_by(device_name=device_name).first()

        if not device_obj:
            return jsonify({'code': 404, 'msg': '未找到该设备'}), 404

        # 2. 调用腾讯云接口获取最新数据
        real_time_data = tencent_handler.get_device_data(device_name)

        if real_time_data:
            current_time = datetime.now()

            # A. 更新本地 Device 表 (实时状态)
            # 遍历返回的数据，如果有对应的字段则更新
            for k, v in real_time_data.items():
                if hasattr(device_obj, k):
                    setattr(device_obj, k, v)
            device_obj.timestamp = current_time

            # B. 插入 DeviceRecord 表 (增加一条历史记录)
            new_record = DeviceRecord(device_name=device_name)
            for k, v in real_time_data.items():
                if hasattr(new_record, k):
                    setattr(new_record, k, v)
            new_record.timestamp = current_time

            # 添加到会话并提交
            db.session.add(new_record)
            db.session.commit()
        else:
            # 如果腾讯云获取失败(例如离线或超时)，打印日志，但依然返回数据库旧数据防止接口崩溃
            print(f"Warning: Sync tencent data failed for {device_name}, returning local cache.")

        # 3. 返回数据 (此时 device_obj 已包含最新 update 的值)
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': device_obj.to_dict()
        })

    except Exception as e:
        db.session.rollback()  # 出错回滚，防止数据库锁死
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ==============================================================================
# 2. 获取设备历史记录 (默认返回最近10条)
# ==============================================================================
@device.route('/record', methods=['GET'])
def device_record():
    try:
        # --- 兼容 URL 参数和 Body JSON ---
        device_name = None
        limit = 10  # 默认值

        if request.args.get('device_name'):
            device_name = request.args.get('device_name')
            if request.args.get('limit'):
                limit = request.args.get('limit')

        if not device_name:
            req_data = request.get_json(silent=True) or {}
            if not req_data and request.get_data():
                try:
                    req_data = json.loads(request.get_data())
                except:
                    pass

            if req_data:
                device_name = req_data.get('device_name')
                if req_data.get('limit'):
                    limit = req_data.get('limit')
        # ----------------------------------

        if not device_name:
            return jsonify({'code': 400, 'msg': '缺少参数: device_name'}), 400

        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        records = DeviceRecord.query.filter_by(device_name=device_name) \
            .order_by(DeviceRecord.timestamp.desc()) \
            .limit(limit) \
            .all()

        data_list = [record.to_dict() for record in records]

        return jsonify({
            'code': 200,
            'msg': 'success',
            'count': len(data_list),
            'data': data_list
        })

    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# ==============================================================================
# 3. 修改设备配置信息
# ==============================================================================
@device.route('/update', methods=['POST'])
def device_update():
    try:
        req_data = request.get_json(silent=True)

        if req_data is None:
            try:
                raw_data = request.get_data()
                if raw_data:
                    req_data = json.loads(raw_data)
                else:
                    req_data = {}
            except:
                return jsonify({'code': 400, 'msg': '无效的 JSON 数据'}), 400

        device_name = req_data.get('device_name')

        if not device_name:
            return jsonify({'code': 400, 'msg': '缺少参数: device_name'}), 400

        device_obj = Device.query.filter_by(device_name=device_name).first()
        if not device_obj:
            return jsonify({'code': 404, 'msg': '未找到该设备'}), 404

        control_fields = [
            'manual_start', 'cycle_mode', 'timer_mode', 'linkage_mode', 'pm_mode',
            'cycle_run_minute', 'cycle_run_second',
            'cycle_stop_minute', 'cycle_stop_second',
            'oil_change_time_setting'
        ]

        local_fields = ['alias', 'longitude', 'latitude']
        allowed_db_fields = control_fields + local_fields

        updated_keys = []
        control_data = {}

        for key, value in req_data.items():
            if key in allowed_db_fields:
                if hasattr(device_obj, key):
                    setattr(device_obj, key, value)
                    updated_keys.append(key)

                if key in control_fields:
                    control_data[key] = value

        if not updated_keys:
            return jsonify({'code': 400, 'msg': '没有提供有效的修改参数'}), 400

        db.session.commit()

        cloud_sync_info = {
            "success": True,
            "message": "Local update only (no control fields changed)",
            "sent_data": {}
        }

        if control_data:
            is_sent = tencent_handler.control_device(device_name, control_data)
            cloud_sync_info["sent_data"] = control_data
            if is_sent:
                cloud_sync_info["message"] = "Sent to device successfully"
            else:
                cloud_sync_info["success"] = False
                cloud_sync_info["message"] = "Failed to send to device"

        return jsonify({
            'code': 200,
            'msg': '更新成功',
            'updated_fields': updated_keys,
            'cloud_sync': cloud_sync_info
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500