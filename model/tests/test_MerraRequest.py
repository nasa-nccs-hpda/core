#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest

import pandas

from osgeo import osr
from osgeo.osr import SpatialReference

from core.model.Envelope import Envelope
from core.model.GeospatialImageFile import GeospatialImageFile
from core.model.MerraRequest import MerraRequest


# -----------------------------------------------------------------------------
# class MerraRequestTestCase
#
# python -m unittest discover model/tests/
# python -m unittest core.model.tests.test_MerraRequest
# -----------------------------------------------------------------------------
class MerraRequestTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # testQueryFiles
    # -------------------------------------------------------------------------
    def testQueryFiles(self):

        existingFiles, missingFiles = \
            MerraRequest.queryFiles(
                pandas.date_range('2010-10-10', '2011-02-12'),
                MerraRequest.MONTHLY,
                ['m2t1nxflx', 'm2t1nxslv'],
                MerraRequest.OPERATIONS)

        baseDir = '/explore/nobackup/projects/ilab/data/MERRA2/Monthly'

        expectedExisting = [
            os.path.join(baseDir, 'm2t1nxflx_avg_2010_month10.nc'),
            os.path.join(baseDir, 'm2t1nxflx_avg_2010_month11.nc'),
            os.path.join(baseDir, 'm2t1nxflx_avg_2010_month12.nc'),
            os.path.join(baseDir, 'm2t1nxflx_avg_2011_month01.nc'),
            os.path.join(baseDir, 'm2t1nxflx_avg_2011_month02.nc'),
            os.path.join(baseDir, 'm2t1nxflx_max_2010_month10.nc'),
            os.path.join(baseDir, 'm2t1nxflx_max_2010_month11.nc'),
            os.path.join(baseDir, 'm2t1nxflx_max_2010_month12.nc'),
            os.path.join(baseDir, 'm2t1nxflx_max_2011_month01.nc'),
            os.path.join(baseDir, 'm2t1nxflx_max_2011_month02.nc'),
            os.path.join(baseDir, 'm2t1nxflx_min_2010_month10.nc'),
            os.path.join(baseDir, 'm2t1nxflx_min_2010_month11.nc'),
            os.path.join(baseDir, 'm2t1nxflx_min_2010_month12.nc'),
            os.path.join(baseDir, 'm2t1nxflx_min_2011_month01.nc'),
            os.path.join(baseDir, 'm2t1nxflx_min_2011_month02.nc'),
            os.path.join(baseDir, 'm2t1nxflx_sum_2010_month10.nc'),
            os.path.join(baseDir, 'm2t1nxflx_sum_2010_month11.nc'),
            os.path.join(baseDir, 'm2t1nxflx_sum_2010_month12.nc'),
            os.path.join(baseDir, 'm2t1nxflx_sum_2011_month01.nc'),
            os.path.join(baseDir, 'm2t1nxflx_sum_2011_month02.nc'),
            os.path.join(baseDir, 'm2t1nxslv_avg_2010_month10.nc'),
            os.path.join(baseDir, 'm2t1nxslv_avg_2010_month11.nc'),
            os.path.join(baseDir, 'm2t1nxslv_avg_2010_month12.nc'),
            os.path.join(baseDir, 'm2t1nxslv_avg_2011_month01.nc'),
            os.path.join(baseDir, 'm2t1nxslv_avg_2011_month02.nc'),
            os.path.join(baseDir, 'm2t1nxslv_max_2010_month10.nc'),
            os.path.join(baseDir, 'm2t1nxslv_max_2010_month11.nc'),
            os.path.join(baseDir, 'm2t1nxslv_max_2010_month12.nc'),
            os.path.join(baseDir, 'm2t1nxslv_max_2011_month01.nc'),
            os.path.join(baseDir, 'm2t1nxslv_max_2011_month02.nc'),
            os.path.join(baseDir, 'm2t1nxslv_min_2010_month10.nc'),
            os.path.join(baseDir, 'm2t1nxslv_min_2010_month11.nc'),
            os.path.join(baseDir, 'm2t1nxslv_min_2010_month12.nc'),
            os.path.join(baseDir, 'm2t1nxslv_min_2011_month01.nc'),
            os.path.join(baseDir, 'm2t1nxslv_min_2011_month02.nc')]

        self.assertEqual(expectedExisting, existingFiles)

        expectedMissing = [
             os.path.join(baseDir, 'm2t1nxslv_sum_2010_month10.nc'),
             os.path.join(baseDir, 'm2t1nxslv_sum_2010_month11.nc'),
             os.path.join(baseDir, 'm2t1nxslv_sum_2010_month12.nc'),
             os.path.join(baseDir, 'm2t1nxslv_sum_2011_month01.nc'),
             os.path.join(baseDir, 'm2t1nxslv_sum_2011_month02.nc')]

        self.assertEqual(expectedMissing, missingFiles)

    # -------------------------------------------------------------------------
    # testAdjustFrequency
    #
    # MerraRequest._adjustFrequency, as a private method, need not be included
    # in the unit test.  This test is helpful at development time, and it won't
    # hurt anything to remain a unit test.
    # -------------------------------------------------------------------------
    def testAdjustFrequency(self):

        # Request an invalid frequency.
        dateRange = pandas.date_range('2010-10-10', '2012-12-12')

        with self.assertRaises(RuntimeError):
            MerraRequest._adjustFrequency(dateRange, 'fortnight')

        # Request monthly.
        monthlyRange = MerraRequest._adjustFrequency(dateRange,
                                                     MerraRequest.MONTHLY)

        self.assertEqual(27, len(monthlyRange))

        expected = ['2010_month10', '2010_month11', '2010_month12',
                    '2011_month01', '2011_month02', '2011_month03',
                    '2011_month04', '2011_month05', '2011_month06',
                    '2011_month07', '2011_month08', '2011_month09',
                    '2011_month10', '2011_month11', '2011_month12',
                    '2012_month01', '2012_month02', '2012_month03',
                    '2012_month04', '2012_month05', '2012_month06',
                    '2012_month07', '2012_month08', '2012_month09',
                    '2012_month10', '2012_month11', '2012_month12']

        self.assertEqual(expected, monthlyRange)

        # Request weekly.
        weeklyRange = MerraRequest._adjustFrequency(dateRange,
                                                    MerraRequest.WEEKLY)

        self.assertEqual(117, len(weeklyRange))

        expected = ['2010_week40', '2010_week41', '2010_week42',
                    '2010_week43', '2010_week44', '2010_week45',
                    '2010_week46', '2010_week47', '2010_week48',
                    '2010_week49', '2010_week50', '2010_week51',
                    '2011_week52', '2011_week01', '2011_week02',
                    '2011_week03', '2011_week04', '2011_week05',
                    '2011_week06', '2011_week07', '2011_week08',
                    '2011_week09', '2011_week10', '2011_week11',
                    '2011_week12', '2011_week13', '2011_week14',
                    '2011_week15', '2011_week16', '2011_week17',
                    '2011_week18', '2011_week19', '2011_week20',
                    '2011_week21', '2011_week22', '2011_week23',
                    '2011_week24', '2011_week25', '2011_week26',
                    '2011_week27', '2011_week28', '2011_week29',
                    '2011_week30', '2011_week31', '2011_week32',
                    '2011_week33', '2011_week34', '2011_week35',
                    '2011_week36', '2011_week37', '2011_week38',
                    '2011_week39', '2011_week40', '2011_week41',
                    '2011_week42', '2011_week43', '2011_week44',
                    '2011_week45', '2011_week46', '2011_week47',
                    '2011_week48', '2011_week49', '2011_week50',
                    '2011_week51', '2012_week52', '2012_week01',
                    '2012_week02', '2012_week03', '2012_week04',
                    '2012_week05', '2012_week06', '2012_week07',
                    '2012_week08', '2012_week09', '2012_week10',
                    '2012_week11', '2012_week12', '2012_week13',
                    '2012_week14', '2012_week15', '2012_week16',
                    '2012_week17', '2012_week18', '2012_week19',
                    '2012_week20', '2012_week21', '2012_week22',
                    '2012_week23', '2012_week24', '2012_week25',
                    '2012_week26', '2012_week27', '2012_week28',
                    '2012_week29', '2012_week30', '2012_week31',
                    '2012_week32', '2012_week33', '2012_week34',
                    '2012_week35', '2012_week36', '2012_week37',
                    '2012_week38', '2012_week39', '2012_week40',
                    '2012_week41', '2012_week42', '2012_week43',
                    '2012_week44', '2012_week45', '2012_week46',
                    '2012_week47', '2012_week48', '2012_week49',
                    '2012_week50', '2012_week51', '2012_week52']

        self.assertEqual(expected, weeklyRange)

    # -------------------------------------------------------------------------
    # testRun
    # -------------------------------------------------------------------------
    def testRun(self):

        ulx = -71
        uly = 40
        lrx = -70
        lry = 39
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        dateRange = pandas.date_range('2010-11-11', '2011-01-12')
        outDir = tempfile.mkdtemp()

        files = MerraRequest.run(env, dateRange, MerraRequest.MONTHLY,
                                 ['m2t1nxslv'], ['QV2M', 'TS'], ['avg'],
                                 outDir)

        expected = [os.path.join(outDir, 'm2t1nxslv_avg_2010_month11_QV2M.nc'),
                    os.path.join(outDir, 'm2t1nxslv_avg_2010_month11_TS.nc'),
                    os.path.join(outDir, 'm2t1nxslv_avg_2010_month12_QV2M.nc'),
                    os.path.join(outDir, 'm2t1nxslv_avg_2010_month12_TS.nc'),
                    os.path.join(outDir, 'm2t1nxslv_avg_2011_month01_QV2M.nc'),
                    os.path.join(outDir, 'm2t1nxslv_avg_2011_month01_TS.nc')]

        self.assertEqual(len(expected), len(files))
        self.assertEqual(expected, sorted(files))

        clipped = GeospatialImageFile(
            os.path.join(outDir, 'm2t1nxslv_avg_2010_month11_QV2M.nc'),
            spatialReference=srs)

        self.assertTrue(clipped.envelope().Equal(env))

        # Delete the clipped files.
        for f in files:
            os.remove(f)
