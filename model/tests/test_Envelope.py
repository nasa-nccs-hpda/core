#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import unittest

from osgeo import gdal
from osgeo import ogr
from osgeo.osr import SpatialReference
from osgeo import osr

from core.model.Envelope import Envelope

gdal.UseExceptions() 


# -----------------------------------------------------------------------------
# class EnvelopeTestCase
#
# https://github.com/OSGeo/gdal/blob/release/3.0/gdal/MIGRATION_GUIDE.TXT
#
# python -m unittest discover model/tests/
# python -m unittest core.model.tests.test_Envelope
# -----------------------------------------------------------------------------
class EnvelopeTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # testAccessors
    # -------------------------------------------------------------------------
    def testAccessors(self):

        ulx = 374187
        uly = 4202663
        lrx = 501598
        lry = 4100640
        srs = SpatialReference()
        srs.ImportFromEPSG(32612)
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        self.assertEqual(ulx, env.ulx())
        self.assertEqual(uly, env.uly())
        self.assertEqual(lrx, env.lrx())
        self.assertEqual(lry, env.lry())

    # -------------------------------------------------------------------------
    # testAddPoint
    # -------------------------------------------------------------------------
    def testAddPoint(self):

        env = Envelope()

        # Invalid x.  Invalid ordinates are undetected by GDAL, so no error.
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        env.addPoint(100, 100, 0, srs)

        # Invalid ordinate type.
        with self.assertRaises(TypeError):
            env.addPoint('abc', 100, 0, srs)

        # Add a second point with a different SRS than the first.
        with self.assertRaisesRegex(RuntimeError, 'must be in the SRS'):

            utm = SpatialReference()
            utm.ImportFromEPSG(32612)
            env.addPoint(374187, 4202663, 0, utm)

        # Add a couple valid points.
        env.addPoint(80, 10, 10, srs)
        env.addPoint(43.5, 79.3, 0, srs)

    # -------------------------------------------------------------------------
    # testAddOgrPoint
    # -------------------------------------------------------------------------
    def testAddOgrPoint(self):

        # ---
        # Several of the tests are covered by testAddPoint because addPoint
        # uses addOgrPoint.
        # ---
        env = Envelope()

        with self.assertRaises(AttributeError):
            env.addOgrPoint('abc')

        with self.assertRaisesRegex(RuntimeError, 'must be of type wkbPoint'):
            env.addOgrPoint(ogr.Geometry(ogr.wkbPolygon))

        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        ogrPt = ogr.Geometry(ogr.wkbPoint)
        ogrPt.AddPoint(20.0, 30.0, 40)
        ogrPt.AssignSpatialReference(srs)
        env.addOgrPoint(ogrPt)

        self.assertEqual(env.ulx(), 20.0)
        self.assertEqual(env.uly(), 30.0)

    # -------------------------------------------------------------------------
    # testExpandByPercentage
    # -------------------------------------------------------------------------
    def testExpandByPercentage(self):

        ulx = 374187
        uly = 4202663
        lrx = 501598
        lry = 4100640
        srs = SpatialReference()
        srs.ImportFromEPSG(32612)
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        env.expandByPercentage(0.0)
        self.assertEqual(ulx, env.ulx())
        self.assertEqual(uly, env.uly())
        self.assertEqual(lrx, env.lrx())
        self.assertEqual(lry, env.lry())

        percentage = 10
        width = 127411.0
        height = 163224.55529116935
        exWidth = width * percentage / 100 / 2.0
        exHeight = height * percentage / 100 / 2.0
        exUlx = abs(ulx - exWidth)
        exUly = abs(uly + exHeight)
        newUlx, newUly, newLrx, newLry = env.expandByPercentage(percentage)
        self.assertEqual(exUlx, newUlx)
        self.assertEqual(exUly, newUly)

    # -------------------------------------------------------------------------
    # testExpansion
    # -------------------------------------------------------------------------
    def testExpansion(self):

        ulx = 374187
        uly = 4202663
        lrx = 501598
        lry = 4100640
        srs = SpatialReference()
        srs.ImportFromEPSG(32612)
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        self.assertEqual(ulx, env.ulx())
        self.assertEqual(uly, env.uly())
        self.assertEqual(lrx, env.lrx())
        self.assertEqual(lry, env.lry())

        lry = 4100000
        env.addPoint(lrx, lry, 0, srs)

        self.assertEqual(ulx, env.ulx())
        self.assertEqual(uly, env.uly())
        self.assertEqual(lrx, env.lrx())
        self.assertEqual(lry, env.lry())

    # -------------------------------------------------------------------------
    # testGetSetState
    # -------------------------------------------------------------------------
    def testGetSetState(self):

        ulx = 374187
        uly = 4202663
        lrx = 501598
        lry = 4100640
        srs = SpatialReference()
        srs.ImportFromEPSG(32612)
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        state = env.__reduce__()
        env2 = Envelope()
        env2.__setstate__(state[2])

        self.assertEqual(env.ulx(), env2.ulx())
        self.assertEqual(env.uly(), env2.uly())
        self.assertEqual(env.lrx(), env2.lrx())
        self.assertEqual(env.lry(), env2.lry())

    # -------------------------------------------------------------------------
    # testTransformTo
    # -------------------------------------------------------------------------
    def testTransformTo(self):

        ulx = 626002.2463251714         # 94.19
        uly = 2145525.859757114         # 19.40
        lrx = 668316.2848759613         # 94.59
        lry = 2112661.4394026464        # 19.10

        srs = SpatialReference()
        srs.ImportFromEPSG(32646)

        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        targetSrs = SpatialReference()
        targetSrs.ImportFromEPSG(4326)
        targetSrs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        env.TransformTo(targetSrs)

        self.assertAlmostEqual(94.199, env.ulx(), places=2)
        self.assertAlmostEqual(19.400, env.uly(), places=2)
        self.assertAlmostEqual(94.599, env.lrx(), places=2)
        self.assertAlmostEqual(19.100, env.lry(), places=2)

    # -------------------------------------------------------------------------
    # testGeographicOrdinateOrder
    # -------------------------------------------------------------------------
    def testGeographicOrdinateOrder(self):

        ulx = -148
        uly = 65
        lrx = -147
        lry = 64
        
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)

        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        self.assertEqual(ulx, env.ulx())
        self.assertEqual(uly, env.uly())
        self.assertEqual(lrx, env.lrx())
        self.assertEqual(lry, env.lry())

    # -------------------------------------------------------------------------
    # testClone
    #
    # Discovered that Envelope.Clone() yields a Geometry, not another Envelope,
    # when using Geometry's implementation.
    # -------------------------------------------------------------------------
    def testClone(self):

        ulx = -148
        uly = 65
        lrx = -147
        lry = 64
        
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)

        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        clone = env.Clone()
        self.assertIsInstance(clone, Envelope)

