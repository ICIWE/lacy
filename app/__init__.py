# -*- coding: utf-8 -*-
# @author: NiHao

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_mail import Mail
from flask_login import LoginManager
from config import config


db = SQLAlchemy()
bootstrap = Bootstrap()
moment = Moment()
mail = Mail()
login_manager = LoginManager()

# 未登录时访问受保护视图，默认重定向到：
login_manager.login_view = 'auth.login'
login_manager.login_message = '没有权限！请登录。'
login_manager.login_message_category = 'info'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[25],
                                      profile_dir=None)

    return app
