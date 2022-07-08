# -*- coding: utf-8 -*-

import os
import unittest

from core.model.BaseFile import BaseFile


# -----------------------------------------------------------------------------
# class BaseFileTestCase
#
# python -m unittest discover model/tests/
# python -m unittest core.model.tests.test_BaseFile
# -----------------------------------------------------------------------------
class BaseFileTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # testFileDoesNotExist
    # -------------------------------------------------------------------------
    def testFileDoesNotExist(self):

        with self.assertRaises(RuntimeError):
            BaseFile('/this/does/not/exist')

    # -------------------------------------------------------------------------
    # testFileExists
    # -------------------------------------------------------------------------
    def testFileExists(self):

        BaseFile(os.path.abspath(__file__))

    # -------------------------------------------------------------------------
    # testNoFileSpecified
    # -------------------------------------------------------------------------
    def testNoFileSpecified(self):

        with self.assertRaises(TypeError):
            BaseFile()

        with self.assertRaises(RuntimeError):
            BaseFile(None)

