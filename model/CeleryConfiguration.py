from celery import Celery
import os


# -----------------------------------------------------------------------------
# CeleryConfiguration
#
# Contains Celery/Redis server configuration
# -----------------------------------------------------------------------------
port = os.environ['REDIS_PORT']

try:
    default_queue = os.environ['CELERY_TASK_DEFAULT_QUEUE']
except KeyError:
    os.environ['CELERY_TASK_DEFAULT_QUEUE'] = str(os.getpid())
    default_queue = os.environ['CELERY_TASK_DEFAULT_QUEUE']

broker = 'redis://'
host = 'localhost'
broker = '{}{}:{}/0'.format(broker, host, port)
backend = broker
pythonpath = './innovation-lab'

# Create context map of key value pairs called 'app'
inclModules = []

app = Celery('innovation-lab',
             backend=backend,
             broker=broker,
             include=inclModules)

app.conf.redis_port = port
app.conf.worker_stdouts_level = 'INFO'
app.conf.task_default_queue = default_queue
app.conf.accept_content = ['application/json',
                           'json',
                           'pickle',
                           'application/x-python-serialize']
