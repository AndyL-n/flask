from flask import Flask
from flex import refresh_token, flex_list
from interval import scheduler
from db import db
from flask_cors import CORS
from views.device import device
from views.site import site
from views.login import login
from views.user import user
from views.union import union
from datetime import datetime


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    scheduler.start()
    import atexit
    atexit.register(lambda: scheduler.shutdown())

    CORS(app, origins='http://localhost:8080')
    app.register_blueprint(login, url_prefix='/login')
    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(device, url_prefix='/device')
    app.register_blueprint(site, url_prefix='/site')
    app.register_blueprint(union, url_prefix='/union')

    with app.app_context():
        # 获取token
        app.config['TOKEN'] = refresh_token(app)

    @app.route('/')
    def index():
        return 'Welcome to JDF!'

    # 修改调度器任务，刷新token
    def refresh_token_with_app():
        with app.app_context():
            app.config['TOKEN'] = refresh_token(app)

    scheduler.add_job(refresh_token_with_app, 'interval', seconds=3600)

    def record():
        with app.app_context():
            from models import Device, DeviceRecord, SiteRecord
            from tencent import tencent_info
            results = db.session.query(Device.box_no, Device.site_no, ).all()
            site_dict = {}
            for box_no, site_no in results:
                # 获取设备信息
                data_dict = tencent_info(box_no)
                if not data_dict:  # 过滤空数据（None或空字典）
                    continue

                # 提取clean_data：保留所有键值对（确保value是有效格式）
                clean_data = {}
                for key, value in data_dict.items():
                    if isinstance(value, dict) and 'Value' in value:
                        clean_data[key] = value['Value']  # 保留所有字段
                if not clean_data:  # 过滤无效的clean_data（无有效字段）
                    continue

                # 创建设备记录并存储所有clean_data
                new_device_record = DeviceRecord(box_no=box_no)
                new_device_record.__dict__.update(clean_data)  # 更新所有字段
                db.session.add(new_device_record)
                db.session.commit()  # 提交设备记录

                # 初始化或更新站点统计（保留所有字段的累加）
                if site_no not in site_dict:
                    # 首次出现的站点：初始化count和所有字段
                    site_dict[site_no] = {'count': 1}
                    # 遍历clean_data的所有键，初始化累加值
                    for key, value in clean_data.items():
                        # 确保值是可累加的（如数字），非数字类型可根据需求处理
                        if isinstance(value, (int, float)):
                            site_dict[site_no][key] = value
                else:
                    # 已存在的站点：count+1，所有字段累加
                    site_dict[site_no]['count'] += 1
                    for key, value in clean_data.items():
                        if isinstance(value, (int, float)) and key in site_dict[site_no]:
                            site_dict[site_no][key] += value
                        elif isinstance(value, (int, float)):
                            # 处理新增字段（之前未出现过的key）
                            site_dict[site_no][key] = value

            # 保存站点统计记录（包含所有字段）
            for site_no, site_data in site_dict.items():
                # 从site_data中排除count（若SiteRecord不需要count字段）
                record_data = {k: v / site_data['count'] for k, v in site_data.items() if k != 'count'}
                # 动态创建SiteRecord，传入所有字段（需确保与模型字段匹配）
                new_site_record = SiteRecord(site_no=site_no, **record_data)
                db.session.add(new_site_record)
                db.session.commit()

    scheduler.add_job(record, 'interval', seconds=5)

    # 刷新设备在线状态
    def connection():
        with app.app_context():
            from models import Device
            response = flex_list(app)
            if response.status_code == 200:
                # 如果请求成功，返回响应内容
                data = response.json()
                # 遍历字典的键值对
                for item in data:
                    for boxReg in item['boxRegs']:
                        existing_device = Device.query.filter_by(box_no=boxReg['box']['boxNo']).first()
                        if existing_device:
                            existing_device.connection_state = boxReg['box']['connectionState']
                            existing_device.timestamp = datetime.now()
                            db.session.commit()

    scheduler.add_job(connection, 'interval', seconds=5)

    return app
