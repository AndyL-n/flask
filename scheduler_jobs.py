import logging
from datetime import datetime

from db import db
from models import Device, DeviceRecord, SiteRecord
from tencent import tencent_handler

logger = logging.getLogger("Scheduler")


def record_job(app):
    with app.app_context():
        try:
            devices = Device.query.filter(Device.delete == 0).all()
            device_list = [{"name": d.device_name, "site_id": d.site_id} for d in devices]

            site_stats = {}

            for item in device_list:
                d_name = item['name']
                sid = item['site_id']

                data = tencent_handler.get_device_data(d_name)
                if not data:
                    continue

                try:
                    device_obj = Device.query.filter_by(device_name=d_name).first()
                    if device_obj:
                        new_record = DeviceRecord(device_name=d_name)
                        for k, v in data.items():
                            if hasattr(new_record, k):
                                setattr(new_record, k, v)
                            if hasattr(device_obj, k):
                                setattr(device_obj, k, v)

                        timestamp = datetime.now()
                        device_obj.timestamp = timestamp
                        if data.get('status') in [1, 2]:
                            device_obj.off_timestamp = timestamp

                        db.session.add(new_record)

                        if sid not in site_stats:
                            site_stats[sid] = {'pm2_5_sum': 0, 'pm10_sum': 0, 'count': 0}

                        pm25 = data.get('pm2_5', 0) or 0
                        pm10 = data.get('pm10', 0) or 0

                        site_stats[sid]['pm2_5_sum'] += int(pm25)
                        site_stats[sid]['pm10_sum'] += int(pm10)
                        site_stats[sid]['count'] += 1

                        db.session.commit()

                except Exception as inner_e:
                    db.session.rollback()
                    logger.error(f"DB update failed for device {d_name}: {str(inner_e)}")

            try:
                for site_id, stats in site_stats.items():
                    if stats['count'] > 0:
                        avg_pm25 = stats['pm2_5_sum'] // stats['count']
                        avg_pm10 = stats['pm10_sum'] // stats['count']

                        new_site_record = SiteRecord(
                            site_id=site_id,
                            pm2_5=avg_pm25,
                            pm10=avg_pm10
                        )
                        db.session.add(new_site_record)
                db.session.commit()
            except Exception as inner_e:
                db.session.rollback()
                logger.error(f"Site average record update failed: {str(inner_e)}")

            logger.info(f"Task finished: {len(device_list)} devices scanned.")

        except Exception as e:
            logger.error(f"Task globally failed: {str(e)}")
