# -*- coding: utf-8 -*-
# @author: NiHao

import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a dog'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.sina.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '0xcce@sina.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    COVER_STORE_PATH = BASE_DIR + '/app/static/'

    LACY_ADMIN = os.environ.get('LACY_ADMIN') or 'li <0xcce@sina.com>'

    SEARCH_BLOOM_FILTER_SIZE = 500      # 搜索模块中，布鲁过滤器的大小

    @staticmethod
    def init_app(app):
        # 备用，以后初始化服务器设置
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLALCHEMY_ECHO = True      # 显示 sqlalchemy 的原始 sql语句
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:0000@localhost/lacy'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:0000@localhost/lacy_test'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:0000@localhost/lacy'


class Config_1(ProductionConfig):
    """docstring for Config_1"""
    
    
    def __init__(self, arg):
        super(Config_1, self).__init__()
        self.arg = arg

        


config = {
    'default': DevelopmentConfig,

    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

