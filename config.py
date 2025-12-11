import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    # 从环境变量读取，如果不存在则报错或使用默认值
    SQLALCHEMY_DATABASE_URI = os.getenv('DB_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False  # 允许返回中文

    # 腾讯云配置
    TENCENT_SECRET_ID = os.getenv('TENCENT_SECRET_ID')
    TENCENT_SECRET_KEY = os.getenv('TENCENT_SECRET_KEY')
    TENCENT_PRODUCT_ID = os.getenv('TENCENT_PRODUCT_ID')