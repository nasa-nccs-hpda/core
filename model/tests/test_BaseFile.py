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

    # -------------------------------------------------------------------------
    # testEq
    # -------------------------------------------------------------------------
    def testEq(self):
        
        bf1 = os.path.abspath(__file__)
        bf2 = bf1
        self.assertEqual(bf1, bf2)
        
        bf3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                           'TSURF.nc')

        self.assertNotEqual(bf1, bf3)  # "unequal" = "not equal"
        