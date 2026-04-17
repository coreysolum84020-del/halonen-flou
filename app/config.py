import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WAVE_API_TOKEN = os.environ.get('WAVE_API_TOKEN', '')
    WAVE_BUSINESS_ID = os.environ.get('WAVE_BUSINESS_ID', '')
    AUTHNET_LOGIN_ID = os.environ.get('AUTHNET_LOGIN_ID', '')
    AUTHNET_TRANSACTION_KEY = os.environ.get('AUTHNET_TRANSACTION_KEY', '')
    QBP_CLIENT_ID = os.environ.get('QBP_CLIENT_ID', '')
    QBP_CLIENT_SECRET = os.environ.get('QBP_CLIENT_SECRET', '')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///halonen_dev.db')

class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    _db_url = os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_DATABASE_URI = _db_url.replace('postgres://', 'postgresql://', 1) if _db_url else ''

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WAVE_API_TOKEN = 'test-wave-token'
    WAVE_BUSINESS_ID = 'test-wave-business-id'
    AUTHNET_LOGIN_ID = 'test-login-id'
    AUTHNET_TRANSACTION_KEY = 'test-transaction-key'
    QBP_CLIENT_ID = 'test-qbp-client-id'
    QBP_CLIENT_SECRET = 'test-qbp-client-secret'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
