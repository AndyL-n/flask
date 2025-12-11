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
            try:
                # 导入优化后的 Handler
                from tencent import tencent_handler
                from models import Device, DeviceRecord, SiteRecord

                # 查询所有未删除的设备
                devices = Device.query.filter(Device.delete == 0).all()
                site_stats = {}  # 用于计算站点平均值

                for device in devices:
                    # 复用连接获取数据
                    data = tencent_handler.get_device_data(device.device_name)

                    if not data:
                        logger.warning(f"No data for device: {device.device_name}")
                        continue

                    # 1. 保存设备历史记录
                    new_record = DeviceRecord(device_name=device.device_name)
                    # 安全地更新属性
                    for k, v in data.items():
                        if hasattr(new_record, k):
                            setattr(new_record, k, v)
                    db.session.add(new_record)

                    # 2. 更新设备实时状态
                    for k, v in data.items():
                        if hasattr(device, k):
                            setattr(device, k, v)
                    # 必须更新时间戳
                    device.timestamp = datetime.now()

                    # 3. 聚合站点数据 (内存中计算)
                    sid = device.site_id
                    if sid not in site_stats:
                        site_stats[sid] = {'pm2_5_sum': 0, 'pm10_sum': 0, 'count': 0}

                    # 确保数据存在且为数字，防止报错
                    pm25 = data.get('pm2_5', 0) or 0
                    pm10 = data.get('pm10', 0) or 0

                    site_stats[sid]['pm2_5_sum'] += int(pm25)
                    site_stats[sid]['pm10_sum'] += int(pm10)
                    site_stats[sid]['count'] += 1

                # 提交设备数据的更改
                db.session.commit()

                # 4. 生成站点平均值记录
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
                logger.info(f"Task finished: {len(devices)} devices updated.")

            except Exception as e:
                db.session.rollback()  # 出错回滚
                logger.error(f"Task failed: {str(e)}")

    # 注册任务
    scheduler.add_job(
        func=record_job,
        trigger='interval',
        # minutes=5,
        seconds=2,
        id='record_data_job',
        replace_existing=True
    )

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=False))

    return app