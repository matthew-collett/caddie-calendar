from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .processor import preflight, process


def init_app(app) -> BackgroundScheduler:
    scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 5,
        }
    )

    scheduler.add_job(
        func=preflight,
        trigger=CronTrigger(hour=17, minute=59, second=30),
        id="preflight",
        replace_existing=True,
    )

    scheduler.add_job(
        func=process,
        trigger=CronTrigger(hour=18, minute=0),
        id="process",
        replace_existing=True,
    )

    scheduler.start()

    # @app.teardown_appcontext
    # def shutdown(exception=None):
    #     if scheduler.running:
    #         app.logger.info("Shutting down scheduler")
    #         scheduler.shutdown(wait=False)

    app.logger.info("Scheduler initialized and started")
    return scheduler


__all__ = ["init_app"]
