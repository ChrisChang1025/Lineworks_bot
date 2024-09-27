from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore      
class Config(object): 
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobstores.db')
    }
    SCHEDULER_API_ENABLED = True

scheduler = APScheduler(BackgroundScheduler(timezone='Asia/Shanghai'))