from flask import Blueprint, request, jsonify
import json
import time
from models import Device, DeviceRecord
from db import db
from tencent import tencent_handler
from datetime import datetime
# 定义蓝图
device = Blueprint('device', __name__)


def apply_cloud_data_to_device(device_obj, cloud_data):
    current_time = datetime.now()
    for key, value in cloud_data.items():
        if hasattr(device_obj, key):
            setattr(device_obj, key, value)

    device_obj.timestamp = current_time
    if cloud_data.get('status') in [1, 2]:
        device_obj.off_timestamp = current_time

    new_record = DeviceRecord(device_name=device_obj.device_name)
    for key, value in cloud_data.items():
        if hasattr(new_record, key):
            setattr(new_record, key, value)

    db.session.add(new_record)


def values_match(actual, expected):
    if isinstance(expected, bool):
        expected = int(expected)
    if isinstance(actual, bool):
        actual = int(actual)

    try:
        return int(actual) == int(expected)
    except (TypeError, ValueError):
        return str(actual) == str(expected)


def wait_for_cloud_data(device_name, expected_data, timeout=30, interval=0.8):
    deadline = time.time() + timeout
    latest_data = None

    while time.time() < deadline:
        latest_data = tencent_handler.get_device_data(device_name)
        if latest_data and all(
            values_match(latest_data.get(key), value)
            for key, value in expected_data.items()
        ):
            return latest_data
        time.sleep(interval)

    return latest_data


def get_status_changes(device_name, limit=120):
    records = DeviceRecord.query.with_entities(DeviceRecord.status, DeviceRecord.timestamp) \
        .filter_by(device_name=device_name) \
        .order_by(DeviceRecord.timestamp.desc()) \
        .limit(limit) \
        .all()

    records.reverse()
    status_changes = []
    last_status = None

    for status, timestamp in records:
        if last_status is None or status != last_status:
            status_changes.append({
                'status': status,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else ""
            })
            last_status = status

    status_changes.reverse()
    return status_changes


def device_snapshot_dict(device_obj):
    return {
        'id': device_obj.id,
        'alias': device_obj.alias,
        'device_name': device_obj.device_name,
        'site_id': device_obj.site_id,
        'site_name': device_obj.site_name,
        'type': device_obj.type,
        'status': device_obj.status,
        'off_timestamp': device_obj.off_timestamp.isoformat() if device_obj.off_timestamp else None,
        'timestamp': device_obj.timestamp.isoformat() if device_obj.timestamp else None,
        'delete': device_obj.delete,
        'manual_start': device_obj.manual_start,
        'cycle_mode': device_obj.cycle_mode,
        'timer_mode': device_obj.timer_mode,
        'linkage_mode': device_obj.linkage_mode,
        'pm_mode': device_obj.pm_mode,
        'cycle_run_minute': device_obj.cycle_run_minute,
        'cycle_run_second': device_obj.cycle_run_second,
        'cycle_stop_minute': device_obj.cycle_stop_minute,
        'cycle_stop_second': device_obj.cycle_stop_second,
        'oil_change_time_setting': device_obj.oil_change_time_setting,
        'pm2_5': device_obj.pm2_5,
        'pm10': device_obj.pm10,
        'cycle_status': device_obj.cycle_status,
        'pump_status': device_obj.pump_status,
        'water_in_status_30': device_obj.water_in_status_30,
        'water_in_status_60': device_obj.water_in_status_60,
        'water_in_status_100': device_obj.water_in_status_100,
        'pitch_angle': device_obj.pitch_angle,
        'horizontal_angle': device_obj.horizontal_angle
    }


@device.route('/snapshot', methods=['GET'])
def device_snapshot():
    try:
        device_name = request.args.get('device_name')
        if not device_name:
            return jsonify({'code': 400, 'msg': '缺少参数: device_name'}), 400

        try:
            limit = max(20, min(int(request.args.get('limit', 120)), 500))
        except (TypeError, ValueError):
            limit = 120

        device_obj = Device.query.filter_by(device_name=device_name).first()
        if not device_obj:
            return jsonify({'code': 404, 'msg': '未找到该设备'}), 404

        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'device': device_snapshot_dict(device_obj),
                'logs': get_status_changes(device_name, limit)
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'msg': str(e)}), 500


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
            apply_cloud_data_to_device(device_obj, real_time_data)
            db.session.commit()
        else:
            # 如果腾讯云获取失败(例如离线或超时)，打印日志，但依然返回数据库旧数据防止接口崩溃
            print(f"Warning: Sync tencent data failed for {device_name}, returning local cache.")

        # 3. 返回数据 (此时 device_obj 已包含最新 update 的值)
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': device_snapshot_dict(device_obj)
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


@device.route('/status_record', methods=['GET'])
def device_status_record():
    try:
        # --- 1. 参数解析 (保持兼容性) ---
        device_name = None

        # 优先 URL 参数
        if request.args.get('device_name'):
            device_name = request.args.get('device_name')

        # 其次 JSON Body
        if not device_name:
            req_data = request.get_json(silent=True) or {}
            # 兼容非标准JSON格式
            if not req_data and request.get_data():
                try:
                    req_data = json.loads(request.get_data())
                except:
                    pass
            if req_data:
                device_name = req_data.get('device_name')

        if not device_name:
            return jsonify({'code': 400, 'msg': '缺少参数: device_name'}), 400


        limit = request.args.get('limit', 500)
        try:
            limit = max(20, min(int(limit), 2000))
        except (TypeError, ValueError):
            limit = 500

        status_changes = get_status_changes(device_name, limit)

        return jsonify({
            'code': 200,
            'msg': 'success',
            'count': len(status_changes),
            'data': status_changes
        })

    except Exception as e:
        # print(e) # 调试用
        return jsonify({'code': 500, 'msg': '服务器内部错误'}), 500

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

        local_updated_keys = []
        control_data = {}

        for key, value in req_data.items():
            if key in allowed_db_fields:
                if key in local_fields and hasattr(device_obj, key):
                    setattr(device_obj, key, value)
                    local_updated_keys.append(key)

                if key in control_fields:
                    control_data[key] = value

        if not local_updated_keys and not control_data:
            return jsonify({'code': 400, 'msg': '没有提供有效的修改参数'}), 400

        cloud_sync_info = {
            "success": True,
            "message": "Local update only (no control fields changed)",
            "sent_data": {}
        }

        if control_data:
            control_result = tencent_handler.control_device(device_name, control_data)
            cloud_sync_info["sent_data"] = control_data
            cloud_sync_info["control_result"] = control_result
            if not control_result.get("success"):
                cloud_data = tencent_handler.get_device_data(device_name)
                if cloud_data:
                    apply_cloud_data_to_device(device_obj, cloud_data)
                    db.session.commit()
                else:
                    db.session.rollback()

                cloud_sync_info["success"] = False
                cloud_sync_info["message"] = "Command was not delivered to device"
                return jsonify({
                    'code': 502,
                    'msg': '腾讯云指令未送达设备，已同步云端当前快照',
                    'cloud_sync': cloud_sync_info,
                    'data': device_snapshot_dict(device_obj)
                })

            cloud_data = wait_for_cloud_data(device_name, control_data)
            if not cloud_data:
                db.session.rollback()
                cloud_sync_info["success"] = False
                cloud_sync_info["message"] = "Sent, but failed to read cloud data"
                return jsonify({
                    'code': 504,
                    'msg': '指令已下发，但未读取到腾讯云最新数据，本地数据未修改',
                    'cloud_sync': cloud_sync_info
                })

            confirmed = all(
                values_match(cloud_data.get(key), value)
                for key, value in control_data.items()
            )
            if not confirmed:
                apply_cloud_data_to_device(device_obj, cloud_data)
                db.session.commit()
                cloud_sync_info["success"] = False
                cloud_sync_info["message"] = "Sent, but cloud data did not change in time"
                cloud_sync_info["latest_data"] = {
                    key: cloud_data.get(key)
                    for key in control_data.keys()
                }
                return jsonify({
                    'code': 504,
                    'msg': '腾讯云目标字段未在等待时间内变化，已同步云端当前快照',
                    'cloud_sync': cloud_sync_info,
                    'data': device_snapshot_dict(device_obj)
                })

            apply_cloud_data_to_device(device_obj, cloud_data)
            cloud_sync_info["message"] = "Cloud data confirmed and saved locally"

        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '更新成功',
            'updated_fields': local_updated_keys + list(control_data.keys()),
            'cloud_sync': cloud_sync_info,
            'data': device_snapshot_dict(device_obj)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': str(e)}), 500
