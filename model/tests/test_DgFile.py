
import unittest

from osgeo import gdal

from core.model.DgFile import DgFile
from core.model.ImageFile import ImageFile


# -----------------------------------------------------------------------------
# class DgFileTestCase
#
# python -m unittest discover model/tests/
# python -m unittest model.tests.test_DgFile
# -----------------------------------------------------------------------------
class DgFileTestCase(unittest.TestCase):

    file_works = '/css/nga/WV01/1B/2008/059/WV01_102001000286BC00_X1BS_052366942010_01/WV01_20080228162641_102001000286BC00_08FEB28162641-P1BS-052366942010_01_P016.tif'
    
    file_noxml = '/css/nga/WV01/1B/2008/059/WV01_1020010001076500_X1BS_005733445010_03/WV01_20080228205612_1020010001076500_08FEB28205612-P1BS-005733445010_03_P001.ntf'

    # -------------------------------------------------------------------------
    # testinit
    # -------------------------------------------------------------------------
    def testinit(self):

        with self.assertRaises(RuntimeError):
            filename = DgFile('/path/to/test.py')

        with self.assertRaises(RuntimeError):
            filename = DgFile('/path/to/test.tif')

        with self.assertRaises(RuntimeError):
            filename = DgFile('bad.tif')

        filename = DgFile(DgFileTestCase.file_works)

        with self.assertRaises(RuntimeError):
            filename = DgFile(DgFileTestCase.file_noxml)

    # -------------------------------------------------------------------------
    # testabscalFactor
    # -------------------------------------------------------------------------
    def testabscalFactor(self):

        fn_w = DgFile(DgFileTestCase.file_works)

        with self.assertRaises(RuntimeError):
            fn_w.abscalFactor('R')

        blue_AF = fn_w.abscalFactor('BAND_P')
        self.assertEqual(blue_AF, 0.06243908)

    # -------------------------------------------------------------------------
    # testToDoubleCheckFootprintsQueryTestFailure
    # -------------------------------------------------------------------------
    def testToDoubleCheckFootprintsQueryTestFailure(self):
        
        DgFile('/css/nga/WV03/1B/2020/021/' +  
               'WV03_104A0100551C7700_A1BS_504127692040_01/' +
               'WV03_20200121115847_104A0100551C7700_20JAN21115847' +
               '-A1BS-504127692040_01_P001.ntf')

    # -------------------------------------------------------------------------
    # testJpeg
    # -------------------------------------------------------------------------
    def testJpeg(self):
        
        DgFile('/css/nga/WV01/1B/2018/250/' +
               'WV01_10200100740C0F00_P1BS_504536069020_01/' +
               'WV01_20180907192956_10200100740C0F00_18SEP07192956' +
               '-P1BS-504536069020_01_P001.ntf')
               