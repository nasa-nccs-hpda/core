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
        # and error text.
        # ---
        lcMsg = str(self.msg.lower())
        hasErrorString = False

        for eMsg in SystemCommand.ERROR_STRINGS_TO_TEST:

            if lcMsg.find(eMsg) != -1:

                hasErrorString = True
                break

        # Other times, the error is reported in stdout.  Detect this.
        if not hasErrorString:

            lcMsg = str(self.stdOut.lower())
            hasErrorString = False

            for eMsg in SystemCommand.ERROR_STRINGS_TO_TEST:

                if lcMsg.find(eMsg) != -1:

                    hasErrorString = True
                    break

        if self.returnCode or hasErrorString:

            if raiseException:

                msg = 'A system command error occurred.  ' + \
                      str(self.stdOut) + \
                      str(self.msg)

                raise RuntimeError(msg)
