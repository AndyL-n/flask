from flask import Flask, g, jsonify, request
from interval import refresh_token, scheduler, device_record
from db import db
from flask_cors import CORS
from views.device import device
from views.site import site
from views.login import login
from views.user import user
from views.union import union

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    scheduler.start()
    # 为了确保APScheduler在Flask应用停止时也能正确关闭，可以注册一个atexit函数
    import atexit
    atexit.register(lambda: scheduler.shutdown())

    CORS(app, origins="http://localhost:8080")
    app.register_blueprint(login, url_prefix='/login')
    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(device, url_prefix='/device')
    app.register_blueprint(site, url_prefix='/site')
    app.register_blueprint(union, url_prefix='/union')

    with app.app_context():
        g.fbox = app.config['FBOX']
        # 获取token
        g.token = refresh_token(app)
        app.config['TOKEN'] = g.token
        # 获取所有设备
        device_record(app)

    # @app.before_request
    # def before_request():
    #     g.fbox = app.config['FBOX']
    #     # 传递app实例
    #     g.token = refresh_token(app)
    #     app.config['TOKEN'] = g.token


    @app.route('/')
    def index():
        print(g.token)
        return 'Welcome to JDF!'

    # 修改调度器任务，刷新token
    def refresh_token_with_app():
        with app.app_context():
            g.token = refresh_token(app)
            app.config['TOKEN'] = g.token
    scheduler.add_job(refresh_token_with_app, 'interval', seconds=3600)

    # # 修改调度器任务，传递app实例
    def device_record_with_app():
        with app.app_context():
            device_record(app)
    scheduler.add_job(device_record_with_app, 'interval', seconds=600)

    return app