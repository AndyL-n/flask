from flask import Flask
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from db import db
from views.site import site
from views.login import login
from views.device import device
from datetime import datetime
import atexit
import logging

# 配置日志打印
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")

scheduler = BackgroundScheduler()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    CORS(app, origins='*')  # 开发阶段允许所有，生产建议指定域名

    app.register_blueprint(login, url_prefix='/login')
    app.register_blueprint(site, url_prefix='/site')
    app.register_blueprint(device, url_prefix='/device')

    @app.route('/')
    def index():
        return 'JDF Backend Service Running.'

    # 定义任务函数
    def record_job():
        with app.app_context():
            from tencent import tencent_handler
            from models import Device, DeviceRecord, SiteRecord

            try:
                # 1. 【分离读取】快速获取设备列表，避免在后续耗时的网络请求中长时间持有数据库锁
                devices = Device.query.filter(Device.delete == 0).all()
                # 将设备信息提取到内存字典中
                device_list = [{"name": d.device_name, "site_id": d.site_id} for d in devices]

                site_stats = {}  # 用于计算站点平均值

                # 2. 遍历设备，单独处理每个设备的网络请求和数据库更新
                for item in device_list:
                    d_name = item['name']
                    sid = item['site_id']

                    # 网络请求（已在 tencent.py 加了超时保护，不会卡死）
                    data = tencent_handler.get_device_data(d_name)

                    if not data:
                        # 没有拿到数据（比如设备不存在），直接跳过，保护系统
                        continue

                    # 3. 【短事务更新】网络请求成功拿到数据后，再开启一次性的数据更新操作
                    try:
                        # 重新查出该设备记录进行更新
                        device_obj = Device.query.filter_by(device_name=d_name).first()
                        if device_obj:
                            # A. 保存设备历史记录
                            new_record = DeviceRecord(device_name=d_name)
                            for k, v in data.items():
                                if hasattr(new_record, k):
                                    setattr(new_record, k, v)
                                # B. 同步更新设备实时状态
                                if hasattr(device_obj, k):
                                    setattr(device_obj, k, v)

                            # C. 更新时间戳
                            timestamp = datetime.now()
                            device_obj.timestamp = timestamp
                            if data.get('status') in [1, 2]:
                                device_obj.off_timestamp = timestamp

                            db.session.add(new_record)

                            # D. 聚合站点数据 (内存中计算)
                            if sid not in site_stats:
                                site_stats[sid] = {'pm2_5_sum': 0, 'pm10_sum': 0, 'count': 0}

                            pm25 = data.get('pm2_5', 0) or 0
                            pm10 = data.get('pm10', 0) or 0

                            site_stats[sid]['pm2_5_sum'] += int(pm25)
                            site_stats[sid]['pm10_sum'] += int(pm10)
                            site_stats[sid]['count'] += 1

                            # 单个设备处理完毕，立刻提交！释放数据库锁
                            db.session.commit()

                    except Exception as inner_e:
                        db.session.rollback()  # 仅回滚当前失败的设备，不影响其他设备
                        logger.error(f"DB update failed for device {d_name}: {str(inner_e)}")

                # 4. 生成站点平均值记录 (采用短事务操作)
                try:
                    for site_id, stats in site_stats.items():
                        if stats['count'] > 0:
                            avg_pm25 = stats['pm2_5_sum'] // stats['count']
                            avg_pm10 = stats['pm10_sum'] // stats['count']

                            new_site_record = SiteRecord(
                                site_id=site_id,
                                pm2_5=avg_pm25,
                                pm10=avg_pm10
                            )
                            db.session.add(new_site_record)
                    db.session.commit()
                except Exception as inner_e:
                    db.session.rollback()
                    logger.error(f"Site average record update failed: {str(inner_e)}")

                logger.info(f"Task finished: {len(device_list)} devices scanned.")

            except Exception as e:
                logger.error(f"Task globally failed: {str(e)}")

    # 注册定时任务
    scheduler.add_job(
        func=record_job,
        trigger='interval',
        minutes=5,
        id='record_data_job',
        replace_existing=True
    )

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))

    return app