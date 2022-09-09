# -*- coding: utf-8 -*-

import os
import unittest

from core.model.BaseFile import BaseFile


# -----------------------------------------------------------------------------
# class BaseFileTestCase
#
# python -m unittest discover core/model/tests/
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

        f1 = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'gsenm_250m_eucl_dist_streams.tif')

        f2 = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'gsenm_250m_eucl_dist_streams.tif')

        self.assertEqual(f1, f2)

        f3 = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'invalid.tif')

        self.assertNotEqual(f1, f3)  # s/b assertUnequal

    # -------------------------------------------------------------------------
    # testLt
    # -------------------------------------------------------------------------
    def testLt(self):

        f1 = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'gsenm_250m_eucl_dist_streams.tif')

        f2 = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'invalid.tif')

        self.assertLess(f1, f2)

    # -------------------------------------------------------------------------
    # testHash
    # -------------------------------------------------------------------------
    def testHash(self):

        f1 = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'gsenm_250m_eucl_dist_streams.tif')

        f2 = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'gsenm_250m_eucl_dist_streams.tif')

        self.assertEqual(hash(f1), hash(f2))

        f3 = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'invalid.tif')

        self.assertNotEqual(hash(f1), hash(f3))
