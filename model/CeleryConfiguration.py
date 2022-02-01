from celery import Celery
from socket import socket
import os


# -----------------------------------------------------------------------------
# CeleryConfiguration
#
# Contains Celery/Redis server configuration
# -----------------------------------------------------------------------------

# Initialize defaults and add to context
port = 6388

with socket() as s:
    s.bind(('', 0))
    # To automatically find a free port, uncomment the next line:
    # port = s.getsockname()[1]

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
app.conf.task_default_queue = '{}'.format(os.getpid())
app.conf.accept_content = ['application/json',
                           'json',
                           'pickle',
                           'application/x-python-serialize']
