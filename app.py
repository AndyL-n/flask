from flask import Flask
from flex import refresh_token
from  interval import scheduler
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

    return app