from db import db  # 从db模块导入db实例
from sqlalchemy import Numeric, DateTime, Boolean, BLOB
from sqlalchemy.orm import relationship
import datetime
from datetime import datetime
import pytz

# 定义东八区时区
tz = pytz.timezone('Asia/Shanghai')


class Site(db.Model):
    __tablename__ = 'site'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    no = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    longitude = db.Column(db.String(255))
    dimension = db.Column(db.String(255))
    address = db.Column(db.String(255))
    street = db.Column(db.String(255))
    type = db.Column(db.String(255))
    end_time = db.Column(db.DateTime)
    start_time = db.Column(db.DateTime)
    info = db.Column(db.String(255))
    delete = db.Column(db.Integer, default='1')
    position_map = db.Column(BLOB)

    # 建立与device表的双向关系
    devices = relationship('Device', backref='site', lazy=True)
    unions = relationship('Union', backref='site', lazy=True)

    def to_dict(self):
        return {
            'no': self.no,
            'name': self.name,
            'longitude': self.longitude,
            'dimension': self.dimension,
            'address': self.address,
            'street': self.street,
            'type': self.type,
            'end_time': str(self.end_time) if self.end_time else None,
            'start_time': str(self.start_time) if self.start_time else None,
            'info': self.info,
            'delete': self.delete,
            'position_map': self.position_map if self.position_map else None
        }


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'name': self.name,
            'password': self.password
        }


class Device(db.Model):
    __tablename__ = 'device'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    alias = db.Column(db.String(255), nullable=False)
    box_no = db.Column(db.String(255), nullable=False, unique=True)
    site_no = db.Column(db.String(255), db.ForeignKey('site.no'), nullable=False)
    site_name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), default='1')
    connection_state = db.Column(db.SmallInteger)  # 对应tinyint(1)
    timestamp = db.Column(DateTime, default=lambda: datetime.now(tz))
    pm_10 = db.Column(Numeric(10, 3))
    pm_2_5 = db.Column(Numeric(10, 3))
    water_pressure = db.Column(Numeric(10, 3))
    phase_a = db.Column(Numeric(10, 3))
    phase_b = db.Column(Numeric(10, 3))
    phase_c = db.Column(Numeric(10, 3))
    water = db.Column(Boolean)  # 对应tinyint(1)
    spray = db.Column(Boolean)  # 对应tinyint(1)
    pm_10_limit = db.Column(Numeric(10, 3))
    pm_2_5_limit = db.Column(Numeric(10, 3))

    # 建立与record表的关系
    records = relationship('Record', backref='device', lazy=True)

    def to_dict(self):
        return {
            'alias': self.alias,
            'box_no': self.box_no,
            'site_no': self.site_no,
            'site_name': self.site_name,
            'type': self.type,
            'connection_state': self.connection_state,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'pm_10': float(self.pm_10) if self.pm_10 else None,
            'pm_2_5': float(self.pm_2_5) if self.pm_2_5 else None,
            'water_pressure': float(self.water_pressure) if self.water_pressure else None,
            'phase_a': float(self.phase_a) if self.phase_a else None,
            'phase_b': float(self.phase_b) if self.phase_b else None,
            'phase_c': float(self.phase_c) if self.phase_c else None,
            'water': self.water,
            'spray': self.spray,
            'pm_10_limit': float(self.pm_10_limit) if self.pm_10_limit else None,
            'pm_2_5_limit': float(self.pm_2_5_limit) if self.pm_2_5_limit else None
        }


class Union(db.Model):
    __tablename__ = 'union'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    site_no = db.Column(db.String(255), db.ForeignKey('site.no'), nullable=False)
    contact = db.Column(db.String(255))
    address = db.Column(db.String(255))
    name = db.Column(db.String(255))
    phone = db.Column(db.String(13))
    type = db.Column(db.String(255))

    def to_dict(self):
        return {
            'site_no': self.site_no,
            'contact': self.contact,
            'address': self.address,
            'name': self.name,
            'phone': self.phone,
            'type': self.type
        }


class Record(db.Model):
    __tablename__ = 'record'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    box_no = db.Column(db.String(32), db.ForeignKey('device.box_no'), nullable=False)
    timestamp = db.Column(DateTime, default=lambda: datetime.now(tz))
    pm2_5 = db.Column(db.String(32))
    pm10 = db.Column(db.String(32))
    water_pressure = db.Column(db.String(32))
    phase_a = db.Column(db.String(32))
    phase_b = db.Column(db.String(32))
    phase_c = db.Column(db.String(32))
    low_water = db.Column(db.String(32))
    spray_status = db.Column(db.String(32))
    mode = db.Column(db.String(32))
    remote = db.Column(db.String(32))
    alarm_reset = db.Column(db.String(32))
    pause_duration = db.Column(db.String(32))
    spray_duration = db.Column(db.String(32))
    water_reset = db.Column(db.String(32))
    pm2_5_limit = db.Column(db.String(32))
    pm10_limit = db.Column(db.String(32))
    current_upper = db.Column(db.String(32))
    current_lower = db.Column(db.String(32))
    monday_enable = db.Column(db.String(32))
    tuesday_enable = db.Column(db.String(32))
    wednesday_enable = db.Column(db.String(32))
    thursday_enable = db.Column(db.String(32))
    friday_enable = db.Column(db.String(32))
    saturday_enable = db.Column(db.String(32))
    sunday_enable = db.Column(db.String(32))
    period_01_enable = db.Column(db.String(32))
    period_01_start_hour = db.Column(db.String(32))
    period_01_start_minute = db.Column(db.String(32))
    period_01_end_hour = db.Column(db.String(32))
    period_01_end_minute = db.Column(db.String(32))
    period_02_enable = db.Column(db.String(32))
    period_02_start_hour = db.Column(db.String(32))
    period_02_start_minute = db.Column(db.String(32))
    period_02_end_hour = db.Column(db.String(32))
    period_02_end_minute = db.Column(db.String(32))
    period_03_enable = db.Column(db.String(32))
    period_03_start_hour = db.Column(db.String(32))
    period_03_start_minute = db.Column(db.String(32))
    period_03_end_hour = db.Column(db.String(32))
    period_03_end_minute = db.Column(db.String(32))
    period_04_enable = db.Column(db.String(32))
    period_04_start_hour = db.Column(db.String(32))
    period_04_start_minute = db.Column(db.String(32))
    period_04_end_hour = db.Column(db.String(32))
    period_04_end_minute = db.Column(db.String(32))
    period_05_enable = db.Column(db.String(32))
    period_05_start_hour = db.Column(db.String(32))
    period_05_start_minute = db.Column(db.String(32))
    period_05_end_hour = db.Column(db.String(32))
    period_05_end_minute = db.Column(db.String(32))
    period_06_enable = db.Column(db.String(32))
    period_06_start_hour = db.Column(db.String(32))
    period_06_start_minute = db.Column(db.String(32))
    period_06_end_hour = db.Column(db.String(32))
    period_06_end_minute = db.Column(db.String(32))
    display_year = db.Column(db.String(32))
    display_month = db.Column(db.String(32))
    display_day = db.Column(db.String(32))
    display_hour = db.Column(db.String(32))
    display_minute = db.Column(db.String(32))
    display_second = db.Column(db.String(32))
    display_week = db.Column(db.String(32))
    setting_year = db.Column(db.String(32))
    setting_month = db.Column(db.String(32))
    setting_day = db.Column(db.String(32))
    setting_hour = db.Column(db.String(32))
    setting_minute = db.Column(db.String(32))
    setting_second = db.Column(db.String(32))
    setting_week = db.Column(db.String(32))
    confirm_clock_modification = db.Column(db.String(32))
    no_1_sprinkler_enable = db.Column(db.String(32))
    no_2_sprinkler_enable = db.Column(db.String(32))
    no_1_sprinkler_automode = db.Column(db.String(32))
    no_2_sprinkler_automode = db.Column(db.String(32))
    no_1_current_angle = db.Column(db.String(32))
    no_2_current_angle = db.Column(db.String(32))
    no_1_sprinkler_setting_angle = db.Column(db.String(32))
    no_2_sprinkler_setting_angle = db.Column(db.String(32))
    no_1_sprinkler_water_valve_start = db.Column(db.String(32))
    no_2_sprinkler_water_valve_start = db.Column(db.String(32))
    no_1_sprinkler_manual_forward_rotation = db.Column(db.String(32))
    no_1_sprinkler_manual_backward_rotation = db.Column(db.String(32))
    no_2_sprinkler_manual_forward_rotation = db.Column(db.String(32))
    no_2_sprinkler_manual_backward_rotation = db.Column(db.String(32))
    no_1_sprinkler_single_circle_pulse = db.Column(db.String(32))
    no_2_sprinkler_single_circle_pulse = db.Column(db.String(32))
    manual_rotation_sprinkler_speed = db.Column(db.String(32))
    automatic_rotation_sprinkler_speed = db.Column(db.String(32))

    def to_dict(self):
        return {
            'box_no': self.box_no,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'pm2_5': self.pm2_5,
            'pm10': self.pm10,
            'water_pressure': self.water_pressure,
            'phase_a': self.phase_a,
            'phase_b': self.phase_b,
            'phase_c': self.phase_c,
            'low_water': self.low_water,
            'spray_status': self.spray_status,
            'mode': self.mode,
            'remote': self.remote,
            'alarm_reset': self.alarm_reset,
            'pause_duration': self.pause_duration,
            'spray_duration': self.spray_duration,
            'water_reset': self.water_reset,
            'pm2_5_limit': self.pm2_5_limit,
            'pm10_limit': self.pm10_limit,
            'current_upper': self.current_upper,
            'current_lower': self.current_lower,
            'monday_enable': self.monday_enable,
            'tuesday_enable': self.tuesday_enable,
            'wednesday_enable': self.wednesday_enable,
            'thursday_enable': self.thursday_enable,
            'friday_enable': self.friday_enable,
            'saturday_enable': self.saturday_enable,
            'sunday_enable': self.sunday_enable,
            'period_01_enable': self.period_01_enable,
            'period_01_start_hour': self.period_01_start_hour,
            'period_01_start_minute': self.period_01_start_minute,
            'period_01_end_hour': self.period_01_end_hour,
            'period_01_end_minute': self.period_01_end_minute,
            'period_02_enable': self.period_02_enable,
            'period_02_start_hour': self.period_02_start_hour,
            'period_02_start_minute': self.period_02_start_minute,
            'period_02_end_hour': self.period_02_end_hour,
            'period_02_end_minute': self.period_02_end_minute,
            'period_03_enable': self.period_03_enable,
            'period_03_start_hour': self.period_03_start_hour,
            'period_03_start_minute': self.period_03_start_minute,
            'period_03_end_hour': self.period_03_end_hour,
            'period_03_end_minute': self.period_03_end_minute,
            'period_04_enable': self.period_04_enable,
            'period_04_start_hour': self.period_04_start_hour,
            'period_04_start_minute': self.period_04_start_minute,
            'period_04_end_hour': self.period_04_end_hour,
            'period_04_end_minute': self.period_04_end_minute,
            'period_05_enable': self.period_05_enable,
            'period_05_start_hour': self.period_05_start_hour,
            'period_05_start_minute': self.period_05_start_minute,
            'period_05_end_hour': self.period_05_end_hour,
            'period_05_end_minute': self.period_05_end_minute,
            'period_06_enable': self.period_06_enable,
            'period_06_start_hour': self.period_06_start_hour,
            'period_06_start_minute': self.period_06_start_minute,
            'period_06_end_hour': self.period_06_end_hour,
            'period_06_end_minute': self.period_06_end_minute,
            'display_year': self.display_year,
            'display_month': self.display_month,
            'display_day': self.display_day,
            'display_hour': self.display_hour,
            'display_minute': self.display_minute,
            'display_second': self.display_second,
            'display_week': self.display_week,
            'setting_year': self.setting_year,
            'setting_month': self.setting_month,
            'setting_day': self.setting_day,
            'setting_hour': self.setting_hour,
            'setting_minute': self.setting_minute,
            'setting_second': self.setting_second,
            'setting_week': self.setting_week,
            'confirm_clock_modification': self.confirm_clock_modification,
            'no_1_sprinkler_enable': self.no_1_sprinkler_enable,
            'no_2_sprinkler_enable': self.no_2_sprinkler_enable,
            'no_1_sprinkler_automode': self.no_1_sprinkler_automode,
            'no_2_sprinkler_automode': self.no_2_sprinkler_automode,
            'no_1_current_angle': self.no_1_current_angle,
            'no_2_current_angle': self.no_2_current_angle,
            'no_1_sprinkler_setting_angle': self.no_1_sprinkler_setting_angle,
            'no_2_sprinkler_setting_angle': self.no_2_sprinkler_setting_angle,
            'no_1_sprinkler_water_valve_start': self.no_1_sprinkler_water_valve_start,
            'no_2_sprinkler_water_valve_start': self.no_2_sprinkler_water_valve_start,
            'no_1_sprinkler_manual_forward_rotation': self.no_1_sprinkler_manual_forward_rotation,
            'no_1_sprinkler_manual_backward_rotation': self.no_1_sprinkler_manual_backward_rotation,
            'no_2_sprinkler_manual_forward_rotation': self.no_2_sprinkler_manual_forward_rotation,
            'no_2_sprinkler_manual_backward_rotation': self.no_2_sprinkler_manual_backward_rotation,
            'no_1_sprinkler_single_circle_pulse': self.no_1_sprinkler_single_circle_pulse,
            'no_2_sprinkler_single_circle_pulse': self.no_2_sprinkler_single_circle_pulse,
            'manual_rotation_sprinkler_speed': self.manual_rotation_sprinkler_speed,
            'automatic_rotation_sprinkler_speed': self.automatic_rotation_sprinkler_speed
        }
