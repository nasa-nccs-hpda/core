#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import logging
import unittest

from core.model.SystemCommand import SystemCommand


# -----------------------------------------------------------------------------
# class SystemCommandTestCase
#
# python -m unittest discover model/tests/
# python -m unittest core.model.tests.test_SystemCommand
# -----------------------------------------------------------------------------
class SystemCommandTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # testInvalidCommand
    # -------------------------------------------------------------------------
    def testInvalidCommand(self):

        with self.assertRaisesRegex(RuntimeError, 'A system command error'):

            SystemCommand('notA_Cmd', None, True)

    # -------------------------------------------------------------------------
    # testValidUnsuccessfulCommand
    # -------------------------------------------------------------------------
    def testValidUnsuccessfulCommand(self):

        scmd = SystemCommand('ls abc.txt')

        # ---
        # Please allow an exception from the PEP formatting because this way
        # is easier to read, considering all the quoting involved.
        # ---
        self.assertEqual(scmd.msg,
            b"ls: cannot access 'abc.txt': No such file or directory\n")

        scmd = SystemCommand('gdalinfo abc.txt', logging.getLogger())
        self.assertTrue(b'ERROR 4: abc.txt: No such file or' in scmd.msg)

        with self.assertRaisesRegex(RuntimeError, 'A system command error'):

            scmd = SystemCommand('gdalinfo abc.txt',
                                 logging.getLogger(),
                                 True)

    # -------------------------------------------------------------------------
    # testValidSuccessfulCommand
    # -------------------------------------------------------------------------
    def testValidSuccessfulCommand(self):

        SystemCommand('ls')
        SystemCommand('ls', logging.getLogger())
        SystemCommand('ls', logging.getLogger(), True)

    # -------------------------------------------------------------------------
    # testExclusionStrings
    # -------------------------------------------------------------------------
    def testExclusionStrings(self):

        # ---
        # It is impractical to run commands that generate the error and
        # exclusion messages that SystemCommand tracks.  Instead, test
        # _detectError directly.
        # ---
        sc = SystemCommand('')

        # Error w/o exclusion
        msg = 'This message has a valid error within it.'
        self.assertTrue(sc._detectError(msg))

        # Exclusion w/o error
        msg = 'This message has a relative error within it.'
        self.assertFalse(sc._detectError(msg))

        # Error w/exclusion
        msg = 'This message has a relative error within it, ' \
              'plus a valid error.'

        self.assertTrue(sc._detectError(msg))
