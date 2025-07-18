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
            from models import Device, Record
            from tencent import tencent_info
            box_nos = db.session.query(Device.box_no).all()
            box_no_list = [box_no[0] for box_no in box_nos]
            for box_no in box_no_list:
                data_dict = tencent_info(box_no)
                if data_dict is None or len(data_dict) == 0:
                    continue
                new_device = Record(box_no=box_no)
                clean_data = {key: value['Value'] for key, value in data_dict.items()}
                # 批量更新属性
                new_device.__dict__.update(clean_data)
                db.session.add(new_device)
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
