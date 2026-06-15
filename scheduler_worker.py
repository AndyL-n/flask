import logging

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

from app import create_app
from scheduler_jobs import record_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")


def main():
    app = create_app()
    scheduler = BlockingScheduler(
        executors={'default': ThreadPoolExecutor(1)},
        job_defaults={
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 60,
        }
    )

    scheduler.add_job(
        func=lambda: record_job(app),
        trigger='interval',
        minutes=5,
        id='record_data_job',
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    logger.info("Scheduler worker started.")
    scheduler.start()


if __name__ == '__main__':
    main()
