from flask import Flask
from flask_cors import CORS
from db import db
from views.site import site
from views.login import login
from views.device import device


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

    return app
