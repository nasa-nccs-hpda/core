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
from osgeo import osr

from core.model.Envelope import Envelope
from core.model.GeospatialImageFile import GeospatialImageFile


# -----------------------------------------------------------------------------
# class GeospatialImageFileTestCase
#
# export PYTHONPATH=`pwd`
#
# python -m unittest discover model/tests/
# python -m unittest core.model.tests.test_GeospatialImageFile
# python -m unittest core.model.tests.test_GeospatialImageFile.GeospatialImageFileTestCase.testInit
# -----------------------------------------------------------------------------
class GeospatialImageFileTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # createTestFile
    # -------------------------------------------------------------------------
    def _createTestFile(self, createUTM=False):

        # ---
        # Set up a logger because serialization was causing loggers to point
        # to the SpatialReferences.
        # ---
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

        testFile = None

        if createUTM:

            testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'gsenm_250m_eucl_dist_streams.tif')

            workingCopy = tempfile.mkstemp(suffix='.tif')[1]
            shutil.copyfile(testFile, workingCopy)

            srs = SpatialReference()
            srs.ImportFromEPSG(32612)

        else:
            testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'TSURF.nc')

            workingCopy = tempfile.mkstemp(suffix='.nc')[1]
            shutil.copyfile(testFile, workingCopy)

            # ---
            # https://github.com/OSGeo/gdal/blob/release/3.0/gdal/
            # MIGRATION_GUIDE.TXT
            # ---
            srs = SpatialReference()
            srs.ImportFromEPSG(4326)
            srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        return GeospatialImageFile(workingCopy, srs, logger)

    # -------------------------------------------------------------------------
    # testClipReproject
    # -------------------------------------------------------------------------
    def testClipReproject(self):

        # ---
        # Test only clipping.
        # ---
        imageFile = self._createTestFile()

        # https://github.com/OSGeo/gdal/blob/release/3.0/gdal/MIGRATION_GUIDE.TXT
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        ulx = -120
        uly = 48
        lrx = -119
        lry = 47
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        imageFile.clipReproject(env)

        # Check the result.
        xform = imageFile._getDataset().GetGeoTransform()
        xScale = xform[1]
        yScale = xform[5]
        width = imageFile._getDataset().RasterXSize
        height = imageFile._getDataset().RasterYSize
        clippedUlx = xform[0]
        clippedUly = xform[3]
        clippedLrx = clippedUlx + width * xScale
        clippedLry = clippedUly + height * yScale

        self.assertAlmostEqual(clippedUlx, ulx)
        self.assertAlmostEqual(clippedUly, uly)
        self.assertAlmostEqual(clippedLrx, lrx)
        self.assertAlmostEqual(clippedLry, lry)

        os.remove(imageFile.fileName())

        # ---
        # Test only reprojection.
        # ---
        imageFile = self._createTestFile(createUTM=True)
        targetSRS = SpatialReference()
        targetSRS.ImportFromEPSG(4326)
        targetSRS.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        imageFile.clipReproject(None, targetSRS)

        # gdaltransform confirms these expected values.
        self.assertTrue(imageFile.srs().IsSame(targetSRS))

        self.assertAlmostEqual(imageFile.envelope().ulx(),
                               -112.5144042,
                               places=7)

        self.assertAlmostEqual(imageFile.envelope().uly(),
                               38.0308143,
                               places=7)

        self.assertAlmostEqual(imageFile.envelope().lrx(),
                               -110.8938763,
                               places=7)

        self.assertAlmostEqual(imageFile.envelope().lry(),
                               36.9934700,
                               places=7)

        os.remove(imageFile.fileName())

        # ---
        # Test clipping and reprojection.
        # ---
        imageFile = self._createTestFile()

        # Build the envelope.
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        ulx = -120
        uly = 48
        lrx = -119
        lry = 47
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        # Reprojection parameter
        targetSRS = SpatialReference()
        targetSRS.ImportFromEPSG(32611)

        # Clip, reproject and resample.
        imageFile.clipReproject(env, targetSRS)

        # Check the results.
        xform = imageFile._getDataset().GetGeoTransform()
        xScale = xform[1]
        yScale = xform[5]
        width = imageFile._getDataset().RasterXSize
        height = imageFile._getDataset().RasterYSize
        clippedUlx = xform[0]
        clippedUly = xform[3]
        clippedLrx = clippedUlx + width * xScale
        clippedLry = clippedUly + height * yScale

        self.assertTrue(imageFile.srs().IsSame(targetSRS))
        self.assertAlmostEqual(clippedUlx, 271930.435, places=3)
        self.assertAlmostEqual(clippedUly, 5318235.614, places=3)
        self.assertAlmostEqual(clippedLrx, 350812.125, places=3)
        self.assertAlmostEqual(clippedLry, 5209532.848, places=3)

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
        # https://github.com/OSGeo/gdal/blob/release/3.0/gdal/MIGRATION_GUIDE.TXT
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

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
        self.assertEqual(type(imageFile.logger), logging.RootLogger)
        
        self.assertNotEqual(imageFile.srs().ExportToProj4(),
                            imageFile2.srs().ExportToProj4())
        
        imageFileDump = imageFile.__getstate__()
        imageFile2.__setstate__(imageFileDump)
        
        self.assertEqual(imageFile.fileName(), imageFile2.fileName())
        self.assertEqual(type(imageFile2.logger), logging.RootLogger)

        # ---
        # The SpatialReference object does not export the same string as the
        # one from which it imports, so we cannot simply compare the round-
        # trip getstate and setstate srs.
        # ---
        # self.assertEqual(imageFile.GetSpatialRef().ExportToProj4(),
        #                  imageFile2.GetSpatialRef().ExportToProj4())

        self.assertEqual(imageFile2.srs().ExportToProj4(),
                         '+proj=longlat +datum=WGS84 +no_defs')

        os.remove(imageFile.fileName())
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
        targetSRS.ImportFromEPSG(32610)

        imageFile.clipReproject(outputSRS=targetSRS)

        # Check the SRS.
        dataset = gdal.Open(imageFile.fileName(), gdalconst.GA_ReadOnly)

        if not dataset:
            raise RuntimeError('Unable to read ' + imageFile.fileName() + '.')

        self.assertTrue(dataset.GetSpatialRef().IsSame(targetSRS))

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

        # https://github.com/OSGeo/gdal/blob/release/3.0/gdal/MIGRATION_GUIDE.TXT
        expectedSRS.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        self.assertTrue(imageFile.srs().IsSame(expectedSRS))

        # Delete the test file.
        os.remove(imageFile.fileName())

    # -------------------------------------------------------------------------
    # testInit
    # -------------------------------------------------------------------------
    def testInit(self):

        testFile1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'gsenm_250m_eucl_dist_streams.tif')

        workingCopy1 = tempfile.mkstemp(suffix='.tif')[1]
        shutil.copyfile(testFile1, workingCopy1)

        # Test valid SRS within the file.
        GeospatialImageFile(workingCopy1)

        # Test invalid SRS within the file.
        testFile2 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'TSURF.nc')

        workingCopy2 = tempfile.mkstemp(suffix='.nc')[1]
        shutil.copyfile(testFile2, workingCopy2)

        with self.assertRaisesRegex(RuntimeError, 'Spatial reference for '):
            GeospatialImageFile(workingCopy2)

        # Test passing an SRS.
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        imageFile = GeospatialImageFile(testFile2, srs)

        expectedSRS = SpatialReference()
        expectedSRS.ImportFromEPSG(4326)
        expectedSRS.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        self.assertTrue(imageFile.srs().IsSame(expectedSRS))

        # Test passing an invalid SRS.
        srs = SpatialReference()

        with self.assertRaisesRegex(RuntimeError, 'Spatial reference for '):
            imageFile = GeospatialImageFile(testFile2, srs)

        os.remove(workingCopy1)
        os.remove(workingCopy2)
