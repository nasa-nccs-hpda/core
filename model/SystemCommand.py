#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import subprocess


# -----------------------------------------------------------------------------
# class SystemCommand
# -----------------------------------------------------------------------------
class SystemCommand(object):

    # ---
    # There are cases where the shell command fails and still returns a 0,
    # causing returnCode to be None.  To detect this, check if msg contains
    # and error text.  These must be in lower case.
    # ---
    ERROR_STRINGS_TO_TEST = ['error',
                             'exception',
                             'not found',
                             'not recognised',
                             'traceback']

    # ---
    # Sometimes, the error strings above cause errors to be detected when there
    # are not really any errors.  Add strings here that are found to cause this
    # problem.
    # ---
    EXCLUSION_STRINGS = ['relative error']

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, cmd, logger=None, raiseException=False):

        if logger:
            logger.info(cmd)

        process = subprocess.Popen(cmd,
                                   shell=True,
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   close_fds=True)

        self.returnCode = process.returncode
        stdOutStdErr = process.communicate()
        self.stdOut = stdOutStdErr[0]
        self.msg = stdOutStdErr[1]

        if logger:

            logger.info('Return code: ' + str(self.returnCode))
            logger.info('Message: ' + str(self.msg))

        # ---
        # There are cases where the shell command fails and still returns a 0,
        # causing returnCode to be None.  To detect this, check if msg contains
        # any error text.  Sometimes there are false positives, where commands
        # emit statements about errors even though they complete successfully.
        # Filter those.
        # ---
        if raiseException and \
            (self.returnCode or
             self._detectError(self.msg) or
             self._detectError(self.stdOut)):

            msg = 'A system command error occurred.  ' + \
                  str(self.stdOut) + \
                  str(self.msg)

            raise RuntimeError(msg)

    # -------------------------------------------------------------------------
    # _detectError
    # -------------------------------------------------------------------------
    def _detectError(self, msg: str) -> bool:

        msg = str(msg.lower())

        # Remove all exclusion strings from the message, ...
        for exclusion in SystemCommand.EXCLUSION_STRINGS:
            msg = ''.join(msg.split(exclusion))

        # ...then search for valid error strings.
        for eMsg in SystemCommand.ERROR_STRINGS_TO_TEST:
            if eMsg in msg:
                return True

        return False
