# -*- coding: utf-8 -*-
import os
from redis import exceptions
import subprocess
import sys

from core.model.CeleryConfiguration import app
from core.model.SystemCommand import SystemCommand


# -----------------------------------------------------------------------------
# class ILProcessController
#
# This class manages the lifecycle of Celery and the Redis server.
# The Python ‘with’  statement is used to manage the Celery lifecycle
# (Sec 8 PEP 343).  The 'with' statement clarifies code that previously would
# use try...finally blocks to ensure that clean-up code is executed.
# This control-flow structure has a basic structure of:
#
#   with expression [as variable]:
#       with-block
#
# The expression is evaluated and results in an object that supports the
# context management protocol (e.g.,has __enter__() and __exit__() methods).
#
# The object's __enter__() is called before with-block is executed and
# therefore can run set-up code. It also may return a value that is bound to
# the name variable, if given. Celery/Redis instantiation occurs here.
#
# After execution of the with-block is finished, the object's __exit__()
# method is called, even if the block raised an exception, and can therefore
# run clean-up code.  Celery/Redis shutdown and cleanup occurs here.  The
# application business logic is what is implemented in the with-block between
# the enter/exit calls.  The remaining structure of the IL client application
# remains unchanged.
#
# Standard Python system utilities (i.e., os.system(), subprocess.run(),
# kill(), pkill()) are used to invoke parameterized commands for:
# a) registering the Celery workers, and
# b) shutting down the Celery workers.
#
# Note that the Redis server is a container-wide daemon. We access the port
# number through an environemt variable.
# -----------------------------------------------------------------------------
class ILProcessController():

    celeryConfig = None

    def __init__(self, celeryConfig) -> None:
        self._celeryConfig = celeryConfig

    # -------------------------------------------------------------------------
    # __enter__
    #
    # Start Redis server and Celery workers
    # -------------------------------------------------------------------------
    def __enter__(self):

        print('In ILProcessController.__enter__() {}'.format(os.getpid()))

        try:

            _backendPort = os.environ['REDIS_PORT']
            print("Redis port = ", _backendPort)

            # Retrieve path to configuration file  - default to model
            ILProcessController.celeryConfig = self._celeryConfig

            # Retrieve concurrency level - default to max available
            _concurrency = app.conf.worker_concurrency
            _concurrency = "" if _concurrency is None \
                else " --concurrency={}".format(_concurrency)

            # Retrieve log level - default to 'info'
            _logLevel = app.conf.worker_stdouts_level
            _logLevel = 'DEBUG' if _logLevel is None \
                else _logLevel

            # Start the Celery Workers
            _worker = "/usr/local/bin/celery -A " + \
                ILProcessController.celeryConfig + " worker " + \
                _concurrency + \
                " --loglevel={}".format(_logLevel) + \
                " &"

            retcode = subprocess.run(_worker,
                                     shell=True,
                                     check=True)
            print(retcode)

        except OSError as e:
            print("Execution failed:", e, file=sys.stderr)

    # -------------------------------------------------------------------------
    # __exit__
    #
    # Shutdown Redis server and Celery workers
    # -------------------------------------------------------------------------

    def __exit__(self, type, value, traceback):

        try:
            print('In ILProcessController.__exit__() {}'.format(os.getpid()))
            processToKill = '\"{} worker\"'.format(
                ILProcessController.celeryConfig)
            # Shutdown the Celery workers
            shutdownWorkers = "/usr/bin/pkill -9 -f {}".format(processToKill)
            SystemCommand(shutdownWorkers, None, True)

        except exceptions.ConnectionError as inst:
            print("Connection Error ignore: {}".format(inst))
        except OSError as e:
            print("Execution failed:", e, file=sys.stderr)
        except Exception as inst:
            print(type(inst))  # the exception instance
            print(inst.args)  # arguments stored in .args
            print(inst)  # __str__ allows args to be printed directly,
