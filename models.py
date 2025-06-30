from db import db  # 从db模块导入db实例

class Site(db.Model):
    __tablename__ = 'site'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    no = db.Column(db.String(255))
    name = db.Column(db.String(255), nullable=False)
    longitude = db.Column(db.String(255))
    dimension = db.Column(db.String(255))
    address = db.Column(db.String(255))
    street = db.Column(db.String(255))
    type = db.Column(db.String(255))
    end_time = db.Column(db.DateTime)
    start_time = db.Column(db.DateTime)
    info = db.Column(db.String(255))
    delete = db.Column(db.Boolean)
    position_map = db.Column(db.BLOB)

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
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    name = db.Column(db.String(255))
    password = db.Column(db.String(255))

    def to_dict(self):
        return {
            'name': self.name,
            'password': self.password
        }


class Device(db.Model):
    __tablename__ = 'device'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    alias = db.Column(db.String(255), nullable=False)
    box_no = db.Column(db.String(255), nullable=False)
    site_no = db.Column(db.String(255), nullable=False)
    site_name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(255), nullable=False)
    connection_state = db.Column(db.SmallInteger)
    pm_10 = db.Column(db.Numeric(10, 3))
    pm_2_5 = db.Column(db.Numeric(10, 3))
    water_pressure = db.Column(db.Numeric(10, 3))
    phase_a = db.Column(db.Numeric(10, 3))
    phase_b = db.Column(db.Numeric(10, 3))
    phase_c = db.Column(db.Numeric(10, 3))
    water = db.Column(db.Boolean)
    spray = db.Column(db.Boolean)
    pm_10_limit = db.Column(db.Numeric(10, 3))
    pm_2_5_limit = db.Column(db.Numeric(10, 3))

    def to_dict(self):
        return {
            'id': self.id,
            'alias': self.alias,
            'box_no': self.box_no,
            'site_no': self.site_no,
            'site_name': self.site_name,
            'type': self.type,
            'connection_state': self.connection_state,
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

class Provider(db.Model):
    __tablename__ = 'provider'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    name = db.Column(db.String(255))
    contact = db.Column(db.String(255))
    number = db.Column(db.String(13))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'number': self.number
        }


class AlarmType(db.Model):
    __tablename__ = 'alarm_type'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)

    def to_dict(self):
        return {
            'id': self.id
        }


class AlarmLog(db.Model):
    __tablename__ = 'alarm_log'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('alarm_type.id', onupdate='NO ACTION', ondelete='NO ACTION'))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id', onupdate='NO ACTION', ondelete='NO ACTION'))

    def to_dict(self):
        return {
            'id': self.id,
            'type_id': self.type_id,
            'device_id': self.device_id
        }


class Monitor(db.Model):
    __tablename__ = 'monitor'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id', onupdate='NO ACTION', ondelete='NO ACTION'))

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id
        }


class Union(db.Model):
    __tablename__ = 'union'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    site_no = db.Column(db.String(255), db.ForeignKey('site.no', onupdate='NO ACTION', ondelete='NO ACTION'))
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


class Scheme(db.Model):
    __tablename__ = 'scheme'
    id = db.Column(db.Integer, nullable=False, autoincrement=True, unique=True, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id', onupdate='NO ACTION', ondelete='NO ACTION'))

    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id
        }
