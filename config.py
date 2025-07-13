class Config:
    # 设置数据库URI
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:admin123@localhost:3306/jdf?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = 'JSON_AS_ASCII'
    FBOX = 'https://openapi.fbox360.com'
    TOKEN = None
