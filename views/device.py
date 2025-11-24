from flask import Blueprint, request, jsonify
import json
from models import Device, DeviceRecord
from db import db
from tencent import tencent_handler
# 定义蓝图
device = Blueprint('device', __name__)

# 1. 获取设备实时详情
@device.route('/info', methods=['GET'])
def device_info():
    try:
        # 获取参数
        req_data = request.get_json(silent=True) or {}
        device_name = req_data.get('device_name')

        if not device_name:
            return jsonify({'code': 400, 'msg': '缺少参数: device_name'}), 400

        # 查询数据库
        device = Device.query.filter_by(device_name=device_name).first()

        if not device:
            return jsonify({'code': 404, 'msg': '未找到该设备'}), 404

        # 返回数据
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': device.to_dict()
        })

    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


# 2. 获取设备历史记录 (默认返回最近10条)
@device.route('/record', methods=['GET'])
def device_record():
    try:
        req_data = request.get_json(silent=True) or {}
        device_name = req_data.get('device_name')
        limit = req_data.get('limit', 10)  # 默认取10条

        if not device_name:
            return jsonify({'code': 400, 'msg': '缺少参数: device_name'}), 400

        # 查询历史记录，按时间倒序排列
        records = DeviceRecord.query.filter_by(device_name=device_name)\
            .order_by(DeviceRecord.timestamp.desc())\
            .limit(limit)\
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

# 3. 修改设备配置信息
@device.route('/update', methods=['POST'])
def device_update():
    try:
        # 获取 JSON 数据
        req_data = request.get_json(silent=True) or {}
        device_name = req_data.get('device_name')

        if not device_name:
            return jsonify({'code': 400, 'msg': '缺少参数: device_name'}), 400

        # 查询设备
        device = Device.query.filter_by(device_name=device_name).first()
        if not device:
            return jsonify({'code': 404, 'msg': '未找到该设备'}), 404

        # ==========================================
        # 1. 定义控制字段 (Control Fields)
        # ==========================================
        # 严格基于物模型 JSON 中 "mode": "rw" 的属性
        control_fields = [
            'manual_start',  # 手动启动
            'cycle_mode',  # 循环模式
            'timer_mode',  # 定时模式
            'linkage_mode',  # 联动模式
            'pm_mode',  # PM模式
            'cycle_run_minute',  # 循环运行_分钟
            'cycle_run_second',  # 循环运行_秒
            'cycle_stop_minute',  # 循环停止_分钟
            'cycle_stop_second',  # 循环停止_秒
            'oil_change_time_setting'  # 换油时间设置
        ]

        # ==========================================
        # 2. 定义数据库允许修改的字段 (Allowed DB Fields)
        # ==========================================
        # 包含：所有控制字段 + 本地管理字段 (别名、GPS)
        # 注意：pitch_angle 和 horizontal_angle 在物模型中为 "r" (只读)，
        #      因此不应通过 update 接口人为修改，应等待设备上报更新。
        local_fields = ['alias', 'longitude', 'latitude']
        allowed_db_fields = control_fields + local_fields

        updated_keys = []
        control_data = {}

        # 遍历请求参数
        for key, value in req_data.items():
            if key in allowed_db_fields:
                # A. 更新本地数据库
                if hasattr(device, key):
                    setattr(device, key, value)
                    updated_keys.append(key)

                # B. 如果属于控制字段，准备下发给腾讯云
                if key in control_fields:
                    control_data[key] = value

        if not updated_keys:
            return jsonify({'code': 400, 'msg': '没有提供有效的修改参数'}), 400

        # 提交到数据库
        db.session.commit()

        # ==========================================
        # 3. 调用腾讯云远程控制
        # ==========================================
        cloud_sync_info = {
            "success": True,
            "message": "Local update only (no control fields changed)",
            "sent_data": {}
        }

        # 只有当 control_data 非空时（即确实修改了 rw 字段），才调用远程接口
        if control_data:
            # 这里的 control_device 使用的是 iotvideo SDK (根据你 tencent.py 的逻辑)
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