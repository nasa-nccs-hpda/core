import logging
import os
import unittest

from osgeo.osr import SpatialReference
from osgeo import osr

from core.model.DgFile import DgFile
from core.model.Envelope import Envelope
from core.model.FootprintsQuery import FootprintsQuery


# ------------------------------------------------------------------------------
# FootprintsQueryTestCase
#
# python -m unittest discover model/tests/
# python -m unittest model.tests.test_FootprintsQuery
# python -m unittest core.model.tests.test_FootprintsQuery.FootprintsQueryTestCase.testAddAoI
# python -m unittest model.tests.test_FootprintsQuery.FootprintsQueryTestCase.testConsistentResults
# ------------------------------------------------------------------------------
class FootprintsQueryTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # setUpClass
    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        cls._logger = logging.getLogger('Test FootprintsQuery')
        cls._logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        cls._logger.addHandler(ch)

    # -------------------------------------------------------------------------
    # testInit
    # -------------------------------------------------------------------------
    def testInit(self):

        FootprintsQuery(FootprintsQueryTestCase._logger)

    # -------------------------------------------------------------------------
    # testAddAoI
    # -------------------------------------------------------------------------
    def testAddAoI(self):

        ulx = 626002.2463251714
        uly = 2145525.859757114
        lrx = 668316.2848759613
        lry = 2112661.4394026464
        srs = SpatialReference()
        srs.ImportFromEPSG(32646)

        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        fpq.addAoI(env)

        numScenes = 27
        fpq.setMaximumScenes(numScenes)
        fpScenes1 = fpq.getScenes()
        self.assertEqual(len(fpScenes1), numScenes)

    # -------------------------------------------------------------------------
    # testConsistentResults
    # -------------------------------------------------------------------------
    def testConsistentResults(self):

        ulx = 94.2
        uly = 19.4
        lrx = 94.6
        lry = 19.1
        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        env = Envelope()
        env.addPoint(ulx, uly, 0, srs)
        env.addPoint(lrx, lry, 0, srs)

        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        fpq.addAoI(env)
        numScenes = 27
        fpq.setMaximumScenes(numScenes)
        fpScenes1 = fpq.getScenes()
        fpScenes2 = fpq.getScenes()

        self.assertEqual(len(fpScenes1), numScenes)
        self.assertEqual(len(fpScenes1), len(fpScenes2))

        for i in range(len(fpScenes1)):
            self.assertEqual(fpScenes1[i].fileName(), fpScenes2[i].fileName())

    # -------------------------------------------------------------------------
    # testSwir
    # -------------------------------------------------------------------------
    def testSwir(self):

        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        fpq.setMaximumScenes(1)
        fpq.setPanchromaticOff()
        fpq.setMultispectralOff()
        fpq.setSwirOn()
        fpScenes1 = fpq.getScenes()

        for ntfPath in fpScenes1:

            dg = DgFile(ntfPath.fileName())
            self.assertEqual(dg.specTypeCode(), 'SWIR')

    # -------------------------------------------------------------------------
    # testWithDgFiles
    # -------------------------------------------------------------------------
    def testWithDgFiles(self):

        # ---
        # We need only one scene to test.  Footprints is unreliable, so
        # collect many scenes to get one valid one.
        # ---
        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        fpq.setMaximumScenes(100)
        fpScenes = fpq.getScenes()

        for fps in fpScenes:

            if os.path.exists(fps.fileName()):

                dg = DgFile(fps.fileName())
                dg.year()
                dg.fileName()

                break

    # -------------------------------------------------------------------------
    # testFpScenesToFileNames
    # -------------------------------------------------------------------------
    def testFpScenesToFileNames(self):

        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        fpq.setMaximumScenes(5)
        fpScenes = fpq.getScenes()
        fileNames = fpq.fpScenesToFileNames(fpScenes)
        foundValidScene = False

        for fileName in fileNames:

            # ---
            # Footprints is unreliable, so  collect several scenes to get at
            # least one valid one.
            # ---
            if os.path.exists(fileName):

                foundValidScene = True
                dg = DgFile(fileName)
                dg.year()
                dg.fileName()

        self.assertTrue(foundValidScene)

    # -------------------------------------------------------------------------
    # testSceneList
    # -------------------------------------------------------------------------
    def testSceneList(self):

        SCENE = '/css/nga/WV01/1B/2015/100/WV01_102001003A7E9A00_X1BS_502788423060_01/WV01_20150410052955_102001003A7E9A00_15APR10052955-P1BS-502788423060_01_P005.ntf'

        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        fpq.setMaximumScenes(5)
        fpq.addScenesFromNtf([SCENE])
        fpScenes = fpq.getScenes()

        self.assertEqual(len(fpScenes), 1)
        self.assertEqual(fpScenes[0].fileName(), SCENE)

    # -------------------------------------------------------------------------
    # testPairNames
    # -------------------------------------------------------------------------
    def testPairNames(self):
        
        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        
        fpq.addPairNames(['WV01_20170327_102001005D2FD200_1020010060DAAC00',
                          'WV01_20180721_10200100742CD900_1020010076241B00'])

        fpScenes = fpq.getScenes()
                
        self.assertEqual(len(fpScenes), 26)
        