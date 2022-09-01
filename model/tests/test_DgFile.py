
import logging
import sys
import unittest

from core.model.DgFile import DgFile


# -----------------------------------------------------------------------------
# class DgFileTestCase
#
# python -m unittest discover model/tests/
# python -m unittest model.tests.test_DgFile
# python -m unittest model.tests.test_DgFile.DgFileTestCase.testSrsError
# -----------------------------------------------------------------------------
class DgFileTestCase(unittest.TestCase):

    file_works = '/css/nga/WV01/1B/2008/059/' + \
                 'WV01_102001000286BC00_X1BS_052366942010_01/' + \
                 'WV01_20080228162641_102001000286BC00_08FEB28162641' + \
                 '-P1BS-052366942010_01_P016.tif'

    file_noxml = '/css/nga/WV01/1B/2008/059/' + \
                 'WV01_1020010001076500_X1BS_005733445010_03/' + \
                 'WV01_20080228205612_1020010001076500_08FEB28205612' +\
                 '-P1BS-005733445010_03_P001.ntf'

    # -------------------------------------------------------------------------
    # testinit
    # -------------------------------------------------------------------------
    def testinit(self):

        with self.assertRaises(RuntimeError):
            filename = DgFile('/path/to/test.py')

        with self.assertRaises(FileNotFoundError):
            filename = DgFile('/path/to/test.tif')

        with self.assertRaises(FileNotFoundError):
            filename = DgFile('bad.tif')

        filename = DgFile(DgFileTestCase.file_works)

        with self.assertRaises(FileNotFoundError):
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

    # -------------------------------------------------------------------------
    # testWV3
    # -------------------------------------------------------------------------
    def testWV3(self):

        dgf = DgFile('/css/nga/WV03/1B/2015/219/' +
                     'WV03_104001000F2D9E00_X1BS_500495393030_01/' +
                     'WV03_20150807213524_104001000F2D9E00_15AUG07213524' +
                     '-M1BS-500495393030_01_P001.ntf')

        dgf.envelope()

    # -------------------------------------------------------------------------
    # testSrsError
    # -------------------------------------------------------------------------
    def testSrsError(self):

        dgf = DgFile('/css/nga/WV02/1B/2010/215/' +
                     'WV02_103001000621E500_X1BS_052807177090_01/' +
                     'WV02_20100803220600_103001000621E500_10AUG03220600' +
                     '-M1BS-052807177090_01_P002.ntf')

        self.assertIsNotNone(dgf._ulx)

    # -------------------------------------------------------------------------
    # testGetSetState
    # -------------------------------------------------------------------------
    def testGetSetState(self):

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

        fileName1 = '/css/nga/WV02/1B/2010/215/' + \
            'WV02_103001000621E500_X1BS_052807177090_01/' + \
            'WV02_20100803220600_103001000621E500_10AUG03220600' + \
            '-M1BS-052807177090_01_P002.ntf'

        dgf = DgFile(fileName1, logger=logger)
        dgfDump = dgf.__getstate__()

        fileName2 = '/css/nga/WV03/1B/2015/219/' + \
            'WV03_104001000F2D9E00_X1BS_500495393030_01/' + \
            'WV03_20150807213524_104001000F2D9E00_15AUG07213524' + \
            '-M1BS-500495393030_01_P001.ntf'

        dgf2 = DgFile(fileName2)
        dgf2.__setstate__(dgfDump)

    # -------------------------------------------------------------------------
    # testGetStripIndex
    # -------------------------------------------------------------------------
    def testGetStripIndex(self):

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

        fileName1 = '/css/nga/WV02/1B/2010/215/' + \
            'WV02_103001000621E500_X1BS_052807177090_01/' + \
            'WV02_20100803220600_103001000621E500_10AUG03220600' + \
            '-M1BS-052807177090_01_P002.ntf'

        dgf = DgFile(fileName1, logger=logger)
        self.assertEqual(dgf.getStripIndex(), 'P002')

        fileName2 = '/css/nga/WV03/1B/2015/219/' + \
            'WV03_104001000F2D9E00_X1BS_500495393030_01/' + \
            'WV03_20150807213524_104001000F2D9E00_15AUG07213524' + \
            '-M1BS-500495393030_01_P001.ntf'

        dgf2 = DgFile(fileName2, logger=logger)
        self.assertEqual(dgf2.getStripIndex(), 'P001')
        self.assertNotEqual(dgf2.getStripIndex(), 'P002')

    # -------------------------------------------------------------------------
    # testIsMate
    # -------------------------------------------------------------------------
    def testIsMate(self):

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)

        fileName1 = '/css/nga/WV02/1B/2018/278/' + \
                    'WV02_10300100889D0300_X1BS_502602073050_01/' + \
                    'WV02_20181005212446_10300100889D0300_18OCT05212446' + \
                    '-P1BS-502602073050_01_P001.ntf'

        fileName2 = '/css/nga/WV02/1B/2018/278/' + \
                    'WV02_10300100869C3C00_X1BS_502599937060_01/' + \
                    'WV02_20181005212317_10300100869C3C00_18OCT05212317' + \
                    '-P1BS-502599937060_01_P001.ntf'

        fileName3 = '/css/nga/WV02/1B/2018/278/' + \
                    'WV02_10300100869C3C00_X1BS_502599937060_01/' + \
                    'WV02_20181005212318_10300100869C3C00_18OCT05212318' + \
                    '-P1BS-502599937060_01_P002.ntf'

        dgf = DgFile(fileName1, logger=logger)
        dgf2 = DgFile(fileName2, logger=logger)
        dgf3 = DgFile(fileName3, logger=logger)

        pairName = 'WV02_20181005_10300100889D0300_10300100869C3C00'

        self.assertTrue(dgf.isMate(pairName, dgf2))
        self.assertTrue(dgf2.isMate(pairName, dgf))
        self.assertFalse(dgf.isMate(pairName, dgf))
        self.assertFalse(dgf.isMate(pairName, dgf3))

        with self.assertRaises(ValueError):
            self.assertFalse(dgf.isMate('junk', dgf2))

    # -------------------------------------------------------------------------
    # testEq
    #
    # Just to ensure the inheritance tree is finding the correct __eq__.
    # -------------------------------------------------------------------------
    def testEq(self):
        
        f1 = '/css/nga/WV02/1B/2015/293/' + \
             'WV02_103001004B456B00_M1BS_506393465060_01/' + \
             'WV02_20151020215510_103001004B456B00_' + \
             '15OCT20215510-M1BS-506393465060_01_P001.ntf'
            
        f2 = '/css/nga/WV02/1B/2015/293/' + \
             'WV02_103001004B456B00_M1BS_506393465060_01/' + \
             'WV02_20151020215510_103001004B456B00_' + \
             '15OCT20215510-M1BS-506393465060_01_P001.ntf'
            
        self.assertEqual(f1, f2)
            
        f3 = '/css/nga/WV02/1B/2015/138/' + \
             'WV02_10300100425E0F00_X1BS_500408334100_01/' + \
             'WV02_20150518220912_10300100425E0F00_' + \
             '15MAY18220912-M1BS-500408334100_01_P001.ntf'
            
        self.assertNotEqual(f1, f3)  # s/b assertUnequal
