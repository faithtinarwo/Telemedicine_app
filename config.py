# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'your_mysql_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'your_mysql_password'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'hospital'
