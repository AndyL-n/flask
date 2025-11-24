from db import db  # 从db模块导入db实例（需确保db初始化正确：含SQLAlchemy实例）
from sqlalchemy import BLOB, DateTime, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

# 定义东八区时区（用于时间字段默认值）
tz = pytz.timezone('Asia/Shanghai')

class User(db.Model):
    """用户表：对应user表，存储系统用户信息"""
    __tablename__ = 'user'

    id = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    name = db.Column(db.String(255), unique=True)  # 用户名，唯一（允许为NULL，SQL中DEFAULT NULL）
    password = db.Column(db.String(255))  # 密码，允许为NULL（实际项目建议非空+加密存储）
    site_id = db.Column(db.Integer, db.ForeignKey('site.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：关联site.id
    delete = db.Column(db.Integer, default=0)  # 逻辑删除标记

    # 关联关系：一个用户对应多个权限记录
    permissions = relationship('Permission', backref='user', lazy=True, foreign_keys='Permission.user_id')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'password': self.password,  # 实际项目中建议隐藏密码（如返回空字符串）
            'site_id': self.site_id,
            'delete': self.delete,
            'site_name': self.site.name if self.site else None  # 关联场地名称（通过backref获取）
        }

class Permission(db.Model):
    """权限表：对应permission表，存储用户-场地的权限关联"""
    __tablename__ = 'permission'

    id = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)  # 自增主键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：关联user.id
    site_id = db.Column(db.Integer, db.ForeignKey('site.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：关联site.id
    site_name = db.Column(db.String(255), db.ForeignKey('site.name', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：关联site.name
    delete = db.Column(db.Integer, default=0)  # 逻辑删除标记

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,  # 关联用户名
            'site_id': self.site_id,
            'site_name': self.site_name,
            'delete': self.delete
        }

class Site(db.Model):
    """场地表：对应site表，存储施工场地基础信息"""
    __tablename__ = 'site'  # 与数据库表名严格一致

    # 字段定义：完全匹配SQL表结构，注意数据类型和约束
    id = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
    no = db.Column(db.String(255), unique=True)  # Fbox组编号，允许为NULL（SQL中DEFAULT NULL）
    name = db.Column(db.String(255), nullable=False, unique=True)  # 场地名称，非空唯一
    longitude = db.Column(db.String(255))  # 经度，允许为NULL
    dimension = db.Column(db.String(255))  # 维度，允许为NULL
    address = db.Column(db.String(255))  # 地址，允许为NULL
    street = db.Column(db.String(255))  # 街道，允许为NULL
    type = db.Column(db.String(255))  # 场地类型，允许为NULL
    start_time = db.Column(DateTime)  # 开始时间，允许为NULL
    end_time = db.Column(DateTime)  # 结束时间，允许为NULL
    info = db.Column(db.String(255))  # 补充信息，允许为NULL
    delete = db.Column(db.Integer, default=0)  # 逻辑删除标记：0=未删除（默认），1=已删除
    position_map = db.Column(BLOB)  # 位置地图（二进制数据），允许为NULL

    # 关联关系：与其他表的双向关联
    # 1. 关联Device表（一个场地对应多个设备）
    devices = relationship('Device', backref='site', lazy=True, foreign_keys='Device.site_id')
    # 2. 关联Union表（一个场地对应多个现场单位）
    unions = relationship('Union', backref='site', lazy=True, foreign_keys='Union.site_id')
    # 3. 关联SiteRecord表（一个场地对应多个场地记录）
    site_records = relationship('SiteRecord', backref='site', lazy=True, foreign_keys='SiteRecord.site_id')
    # 4. 关联Permission表（一个场地对应多个权限记录）
    permissions = relationship('Permission', backref='site', lazy=True, foreign_keys='Permission.site_id')
    # 5. 关联User表（一个场地对应多个用户）
    users = relationship('User', backref='site', lazy=True, foreign_keys='User.site_id')

    def to_dict(self):
        """将模型实例转为字典，便于接口返回JSON"""
        return {
            'id': self.id,
            'no': self.no,
            'name': self.name,
            'longitude': self.longitude,
            'dimension': self.dimension,
            'address': self.address,
            'street': self.street,
            'type': self.type,
            'start_time': self.start_time.isoformat() if self.start_time else None,  # 时间转ISO格式字符串
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'info': self.info,
            'delete': self.delete,
            'position_map': self.position_map.hex() if self.position_map else None  # BLOB转16进制字符串（避免二进制传输问题）
        }

class SiteRecord(db.Model):
    """场地记录表：对应SQL的site_record表，存储场地历史环境数据"""
    __tablename__ = 'site_record'

    id = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)  # 自增主键
    site_id = db.Column(db.Integer, db.ForeignKey('site.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：场地ID
    pm2_5 = db.Column(db.Integer, default=0)  # 场地PM2.5浓度（mg/m³，默认0）
    pm10 = db.Column(db.Integer, default=0)  # 场地PM10浓度（mg/m³，默认0）
    timestamp = db.Column(DateTime, default=lambda: datetime.now(tz), onupdate=lambda: datetime.now(tz))  # 记录时间
    delete = db.Column(db.Integer, default=0)  # 逻辑删除标记

    def to_dict(self):
        return {
            'id': self.id,
            'site_id': self.site_id,
            'pm2_5': self.pm2_5,
            'pm10': self.pm10,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'delete': self.delete
        }

class Union(db.Model):
    """现场单位表：对应union表，存储场地关联的单位信息"""
    __tablename__ = 'union'

    id = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)  # 自增主键
    site_id = db.Column(db.Integer, db.ForeignKey('site.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：场地ID
    contact = db.Column(db.String(255))  # 联系人，允许为NULL
    address = db.Column(db.String(255))  # 单位地址，允许为NULL
    name = db.Column(db.String(255))  # 单位名称，允许为NULL
    phone = db.Column(db.String(13))  # 联系电话（长度13，适配手机号），允许为NULL
    type = db.Column(db.String(255))  # 单位类型，允许为NULL
    delete = db.Column(db.Integer, default=0)  # 逻辑删除标记

    def to_dict(self):
        return {
            'id': self.id,
            'site_id': self.site_id,
            'site_name': self.site.name if self.site else None,  # 关联场地名称
            'contact': self.contact,
            'address': self.address,
            'name': self.name,
            'phone': self.phone,
            'type': self.type,
            'delete': self.delete
        }

class Device(db.Model):
    """设备表：对应device表，存储设备基础信息和状态"""
    __tablename__ = 'device'

    # 字段严格匹配SQL：注意主键是device_name（非id）
    id = db.Column(db.Integer, nullable=False)  # 设备ID（非自增，需手动传入）
    alias = db.Column(db.String(255), nullable=False)  # 设备别名，非空
    device_name = db.Column(db.String(255), nullable=False, unique=True, primary_key=True)  # 设备名称（主键+唯一）
    site_id = db.Column(db.Integer, db.ForeignKey('site.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：关联site.id
    site_name = db.Column(db.String(255), db.ForeignKey('site.name', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：关联site.name
    longitude = db.Column(DECIMAL(10, 6))  # 对应 SQL 的 decimal(10,6)
    latitude = db.Column(DECIMAL(10, 6))
    type = db.Column(db.String(255), nullable=False)  # 设备类型，非空
    status = db.Column(db.Integer, default=0)  # 在线状态：1=在线，0=离线（默认0）
    timestamp = db.Column(DateTime, default=lambda: datetime.now(tz), onupdate=lambda: datetime.now(tz))  # 时间戳（更新时自动刷新）
    delete = db.Column(db.Integer, default=0)  # 逻辑删除标记
    # 设备控制/状态字段
    manual_start = db.Column(db.Integer, default=0)  # 手动启动：0=关闭，1=启动
    cycle_mode = db.Column(db.Integer, default=0)  # 循环模式
    timer_mode = db.Column(db.Integer, default=0)  # 定时模式
    linkage_mode = db.Column(db.Integer, default=0)  # 联动模式
    pm_mode = db.Column(db.Integer, default=0)  # PM模式
    cycle_run_minute = db.Column(db.Integer, default=0)  # 循环运行-分钟
    cycle_run_second = db.Column(db.Integer, default=0)  # 循环运行-秒
    cycle_stop_minute = db.Column(db.Integer, default=0)  # 循环停止-分钟
    cycle_stop_second = db.Column(db.Integer, default=0)  # 循环停止-秒
    oil_change_time_setting = db.Column(db.Integer, default=0)  # 换油时间设置（分钟）
    pm2_5 = db.Column(db.Integer, default=0)  # PM2.5浓度（mg/m³）
    pm10 = db.Column(db.Integer, default=0)  # PM10浓度（mg/m³）
    cycle_status = db.Column(db.Integer, default=0)  # 循环状态
    pump_status = db.Column(db.Integer, default=0)  # 水泵状态
    water_in_status_30 = db.Column(db.Integer, default=0)  # 进水进度30%
    water_in_status_60 = db.Column(db.Integer, default=0)  # 进水进度60%
    water_in_status_100 = db.Column(db.Integer, default=0)  # 进水进度100%
    pitch_angle = db.Column(db.Integer, default=0)  # 俯角（-90~90度）
    horizontal_angle = db.Column(db.Integer, default=0)  # 水平角（0~359度）

    # 关联关系：一个设备对应多个设备记录
    device_records = relationship('DeviceRecord', backref='device', lazy=True, foreign_keys='DeviceRecord.device_name')

    def to_dict(self):
        return {
            'id': self.id,
            'alias': self.alias,
            'device_name': self.device_name,
            'site_id': self.site_id,
            'site_name': self.site_name,
            'type': self.type,
            'status': '在线' if self.status == 1 else '离线',  # 状态转文字描述
            'longitude': float(self.longitude) if self.longitude is not None else None,
            'latitude': float(self.latitude) if self.latitude is not None else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'delete': self.delete,
            # 设备控制/状态字段
            'manual_start': self.manual_start,
            'cycle_mode': self.cycle_mode,
            'timer_mode': self.timer_mode,
            'linkage_mode': self.linkage_mode,
            'pm_mode': self.pm_mode,
            'cycle_run_minute': self.cycle_run_minute,
            'cycle_run_second': self.cycle_run_second,
            'cycle_stop_minute': self.cycle_stop_minute,
            'cycle_stop_second': self.cycle_stop_second,
            'oil_change_time_setting': self.oil_change_time_setting,
            'pm2_5': self.pm2_5,
            'pm10': self.pm10,
            'cycle_status': self.cycle_status,
            'pump_status': self.pump_status,
            'water_in_status_30': self.water_in_status_30,
            'water_in_status_60': self.water_in_status_60,
            'water_in_status_100': self.water_in_status_100,
            'pitch_angle': self.pitch_angle,
            'horizontal_angle': self.horizontal_angle
        }

class DeviceRecord(db.Model):
    """设备记录表：对应device_record表，存储设备历史状态"""
    __tablename__ = 'device_record'

    id = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)  # 记录ID（自增主键）
    device_name = db.Column(db.String(255), db.ForeignKey('device.device_name', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False)  # 外键：关联device.device_name
    status = db.Column(db.Integer, default=0)  # 设备状态（同Device表）
    # 设备历史状态字段（与Device表对应）
    manual_start = db.Column(db.Integer, default=0)
    cycle_mode = db.Column(db.Integer, default=0)
    timer_mode = db.Column(db.Integer, default=0)
    linkage_mode = db.Column(db.Integer, default=0)
    pm_mode = db.Column(db.Integer, default=0)
    cycle_run_minute = db.Column(db.Integer, default=0)
    cycle_run_second = db.Column(db.Integer, default=0)
    cycle_stop_minute = db.Column(db.Integer, default=0)
    cycle_stop_second = db.Column(db.Integer, default=0)
    oil_change_time_setting = db.Column(db.Integer, default=0)
    pm2_5 = db.Column(db.Integer, default=0)
    pm10 = db.Column(db.Integer, default=0)
    cycle_status = db.Column(db.Integer, default=0)
    pump_status = db.Column(db.Integer, default=0)
    water_in_status_30 = db.Column(db.Integer, default=0)
    water_in_status_60 = db.Column(db.Integer, default=0)
    water_in_status_100 = db.Column(db.Integer, default=0)
    pitch_angle = db.Column(db.Integer, default=0)
    horizontal_angle = db.Column(db.Integer, default=0)
    timestamp = db.Column(DateTime, default=lambda: datetime.now(tz), onupdate=lambda: datetime.now(tz))  # 记录时间
    delete = db.Column(db.Integer, default=0)  # 逻辑删除标记

    def to_dict(self):
        return {
            'id': self.id,
            'device_name': self.device_name,
            'device_alias': self.device.alias if self.device else None,  # 关联设备别名
            'status': '在线' if self.status == 1 else '离线',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'delete': self.delete,
            # 设备历史状态字段
            'manual_start': self.manual_start,
            'cycle_mode': self.cycle_mode,
            'timer_mode': self.timer_mode,
            'linkage_mode': self.linkage_mode,
            'pm_mode': self.pm_mode,
            'cycle_run_minute': self.cycle_run_minute,
            'cycle_run_second': self.cycle_run_second,
            'cycle_stop_minute': self.cycle_stop_minute,
            'cycle_stop_second': self.cycle_stop_second,
            'oil_change_time_setting': self.oil_change_time_setting,
            'pm2_5': self.pm2_5,
            'pm10': self.pm10,
            'cycle_status': self.cycle_status,
            'pump_status': self.pump_status,
            'water_in_status_30': self.water_in_status_30,
            'water_in_status_60': self.water_in_status_60,
            'water_in_status_100': self.water_in_status_100,
            'pitch_angle': self.pitch_angle,
            'horizontal_angle': self.horizontal_angle
        }
