import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-in-production")
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "password")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "sunoyaar")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
