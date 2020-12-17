#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import logging
import os
import shutil
import sys
import tempfile
import unittest

from osgeo import gdal
from osgeo import gdalconst
from osgeo.osr import SpatialReference

from core.model.Envelope import Envelope
from core.model.GeospatialImageFile import GeospatialImageFile
from core.model.ImageFile import ImageFile


# -----------------------------------------------------------------------------
# class GeospatialImageFileTestCase
#
# singularity shell -B /att /att/nobackup/iluser/containers/ilab-core-5.0.0.simg
# cd to the directory containing core
# export PYTHONPATH=`pwd`
# python -m unittest discover model/tests/
# python -m unittest model.tests.test_GeospatialImageFile
# -----------------------------------------------------------------------------
class GeospatialImageFileTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # createTestFile
    # -------------------------------------------------------------------------
    def _createTestFile(self):

        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'TSURF.nc')

        workingCopy = tempfile.mkstemp(suffix='.nc')[1]
        shutil.copyfile(testFile, workingCopy)
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        return GeospatialImageFile(workingCopy, srs)

    # -------------------------------------------------------------------------
    # testClipReproject
    # -------------------------------------------------------------------------
    def testClipReproject(self):

        # Build the test file.
        imageFile = self._createTestFile()

        # Build the envelope.
        ulx = 367080
        uly = 4209230
        lrx = 509200
        lry = 4095100
        srs = SpatialReference()
        srs.ImportFromEPSG(32612)
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        # Reprojection parameter
        targetSRS = SpatialReference()
        targetSRS.ImportFromEPSG(4326)

        # Clip, reproject and resample.
        imageFile.clipReproject(env, targetSRS,)

        # Check the results.
        dataset = gdal.Open(imageFile.fileName(), gdalconst.GA_ReadOnly)

        if not dataset:
            raise RuntimeError('Unable to read ' + imageFile.fileName() + '.')

        xform = dataset.GetGeoTransform()
        xScale = xform[1]
        yScale = xform[5]
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        clippedUlx = xform[0]
        clippedUly = xform[3]
        clippedLrx = clippedUlx + width * xScale
        clippedLry = clippedUly + height * yScale

        self.assertAlmostEqual(clippedUlx, -112.49369402670872, places=12)
        self.assertAlmostEqual(clippedUly, 38.03073206024332, places=11)
        self.assertAlmostEqual(clippedLrx, -110.89516946364738, places=12)
        self.assertAlmostEqual(clippedLry, 36.99265291293727, places=11)

        outSRS = SpatialReference()
        outSRS.ImportFromWkt(dataset.GetProjection())
        self.assertTrue(outSRS.IsSame(targetSRS))

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testClip
    # -------------------------------------------------------------------------
    def testClip(self):

        # Build the test file.
        imageFile = self._createTestFile()

        # Build the envelope and clip.
        ulx = -100
        uly = 40
        lrx = -70
        lry = 30
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)
        imageFile.clipReproject(env)

        # Check the corners.
        dataset = gdal.Open(imageFile.fileName(), gdalconst.GA_ReadOnly)

        if not dataset:
            raise RuntimeError('Unable to read ' + imageFile.fileName() + '.')

        xform = dataset.GetGeoTransform()
        xScale = xform[1]
        yScale = xform[5]
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        clippedUlx = xform[0]
        clippedUly = xform[3]
        clippedLrx = ulx + width * xScale
        clippedLry = uly + height * yScale

        self.assertEqual(clippedUlx, ulx)
        self.assertEqual(clippedUly, uly)
        self.assertEqual(clippedLrx, lrx)
        self.assertEqual(clippedLry, lry)

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testEnvelope
    # -------------------------------------------------------------------------
    def testEnvelope(self):

        # Create a test image.
        imageFile = self._createTestFile()

        # Test envelope.
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        expectedEnvelope = Envelope()
        expectedEnvelope.addPoint(-125.3125000,  50.25, 0, srs)
        expectedEnvelope.addPoint(-65.9375000,  23.75, 0, srs)

        self.assertTrue(imageFile.envelope().Equals(expectedEnvelope))

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testGetSquareScale
    # -------------------------------------------------------------------------
    def testGetSquareScale(self):

        imageFile = self._createTestFile()
        self.assertEqual(imageFile.getSquareScale(), 0.625)
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testGetSetState
    # -------------------------------------------------------------------------
    def testGetSetState(self):

        imageFile = self._createTestFile()

        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'TSURF.nc')

        workingCopy = tempfile.mkstemp(suffix='.nc')[1]
        shutil.copyfile(testFile, workingCopy)
        srs = SpatialReference()
        srs.ImportFromEPSG(32612)
        imageFile2 = GeospatialImageFile(workingCopy, srs)

        self.assertNotEqual(imageFile.fileName(), imageFile2.fileName())

        self.assertNotEqual(imageFile.srs().ExportToProj4(),
                            imageFile2.srs().ExportToProj4())

        imageFileDump = imageFile.__getstate__()
        imageFile2.__setstate__(imageFileDump)

        self.assertEqual(imageFile.fileName(), imageFile2.fileName())

        #---
        # The SpatialReference object does not export the same string as the
        # one from which it imports, so we cannot simply compare the round-
        # trip getstate and setstate srs.
        #---
        # self.assertEqual(imageFile.srs().ExportToProj4(),
        #                  imageFile2.srs().ExportToProj4())

        self.assertEqual(imageFile2.srs().ExportToProj4(),
                         '+proj=longlat +datum=WGS84 +no_defs')

        os.remove(imageFile.fileName())
        os.remove(workingCopy)

    # -------------------------------------------------------------------------
    # testInvalidSpatialReference
    # -------------------------------------------------------------------------
    def testInvalidSpatialReference(self):

        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'TSURF.nc')

        workingCopy = tempfile.mkstemp(suffix='.nc')[1]
        shutil.copyfile(testFile, workingCopy)

        with self.assertRaisesRegex(RuntimeError, 'Spatial reference for '):
            GeospatialImageFile(workingCopy, SpatialReference())

        os.remove(workingCopy)

    # -------------------------------------------------------------------------
    # testNoOperation
    # -------------------------------------------------------------------------
    def testNoOperation(self):

        # Create a test image.
        imageFile = self._createTestFile()

        # Test with no operation specified.
        with self.assertRaisesRegex(RuntimeError, 'envelope or output SRS'):
            imageFile.clipReproject()

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testReproject
    # -------------------------------------------------------------------------
    def testReproject(self):

        # Build the test file.
        imageFile = self._createTestFile()

        # Reproject.
        targetSRS = SpatialReference()
        targetSRS.ImportFromEPSG(4326)
        imageFile.clipReproject(outputSRS=targetSRS)

        # Check the SRS.
        dataset = gdal.Open(imageFile.fileName(), gdalconst.GA_ReadOnly)

        if not dataset:
            raise RuntimeError('Unable to read ' + imageFile.fileName() + '.')

        outSRS = SpatialReference()
        outSRS.ImportFromWkt(dataset.GetProjection())
        self.assertTrue(outSRS.IsSame(targetSRS))

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testResample
    # -------------------------------------------------------------------------
    def testResample(self):

        # Build the test file.
        imageFile = self._createTestFile()

        # Scale.  Original scale is (246, -246).
        targetX_Scale = 0.25
        targetY_Scale = -0.35

        imageFile.resample(targetX_Scale, targetY_Scale)

        # Check the scale.
        dataset = gdal.Open(imageFile.fileName(), gdalconst.GA_ReadOnly)

        if not dataset:
            raise RuntimeError('Unable to read ' + imageFile.fileName() + '.')

        xform = dataset.GetGeoTransform()
        self.assertEqual(xform[1], targetX_Scale)
        self.assertAlmostEqual(xform[5], targetY_Scale, places=2)

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testScale
    # -------------------------------------------------------------------------
    def testScale(self):

        # Build the test file.
        imageFile = self._createTestFile()

        # Check the scale.
        self.assertEqual(imageFile.scale()[0], 0.625)
        self.assertEqual(imageFile.scale()[1], -0.5)

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testSrs
    # -------------------------------------------------------------------------
    def testSrs(self):

        # Build the test file.
        imageFile = self._createTestFile()

        # Check the srs.
        expectedSRS = SpatialReference()
        expectedSRS.ImportFromEPSG(4326)
        self.assertTrue(imageFile.srs().IsSame(expectedSRS))

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testImageToGround
    # -------------------------------------------------------------------------
    def testImageToGround(self):
        
        imageFile = self._createTestFile()
        xSize = imageFile._getDataset().RasterXSize
        ySize = imageFile._getDataset().RasterYSize
        
        # Upper-left
        ulImage = (0, 0)
        groundPt = imageFile.imageToGround(ulImage[0], ulImage[1])
        ulGround = (-125.3125,  50.25)  # from gdalinfo
        self.assertEqual(groundPt, ulGround)

        # Lower-left
        llImage = (0, ySize)
        groundPt = imageFile.imageToGround(llImage[0], llImage[1])
        llGround = (-125.3125,  23.75)
        self.assertEqual(groundPt, llGround)

        # Upper-right
        urImage = (xSize, 0)
        groundPt = imageFile.imageToGround(urImage[0], urImage[1])
        urGround = (-65.9375, 50.25)
        self.assertEqual(groundPt, urGround)

        # Lower-right
        lrImage = (xSize, ySize)
        groundPt = imageFile.imageToGround(lrImage[0], lrImage[1])
        lrGround = (-65.9375000,  23.75)
        self.assertEqual(groundPt, lrGround)
        
        # Center
        cImage = (xSize/2, ySize/2)
        groundPt = imageFile.imageToGround(cImage[0], cImage[1])
        cGround = (-95.625,  37.0)
        self.assertEqual(groundPt, cGround)
        
        os.remove(imageFile.fileName())
        
    # -------------------------------------------------------------------------
    # testGroundToImage
    # -------------------------------------------------------------------------
    def testGroundToImage(self):
        
        imageFile = self._createTestFile()
        xSize = imageFile._getDataset().RasterXSize
        ySize = imageFile._getDataset().RasterYSize
        
        # Upper-left
        ulGround = (-125.3125,  50.25)  # from gdalinfo
        imagePt = imageFile.groundToImage(ulGround[0], ulGround[1])
        ulImage = (0, 0)
        self.assertEqual(imagePt, ulImage)

        # Lower-left
        llGround = (-125.3125,  23.75)
        imagePt = imageFile.groundToImage(llGround[0], llGround[1])
        llImage = (0, ySize)
        self.assertEqual(imagePt, llImage)

        # Upper-right
        urGround = (-65.9375, 50.25)
        imagePt = imageFile.groundToImage(urGround[0], urGround[1])
        urImage = (xSize, 0)
        self.assertEqual(imagePt, urImage)

        # Lower-right
        lrGround = (-65.9375000,  23.75)
        imagePt = imageFile.groundToImage(lrGround[0], lrGround[1])
        lrImage = (xSize, ySize)
        self.assertEqual(imagePt, lrImage)

        # Center
        cGround = (-95.625,  37.0)
        imagePt = imageFile.groundToImage(cGround[0], cGround[1])
        cImage = (int(xSize/2), int(ySize/2))
        self.assertEqual(imagePt, cImage)
        
        # Round-trip
        cImage = (xSize/2, ySize/2)
        groundPt = imageFile.imageToGround(cImage[0], cImage[1])
        self.assertEqual(groundPt, cGround)

        os.remove(imageFile.fileName())
        
        