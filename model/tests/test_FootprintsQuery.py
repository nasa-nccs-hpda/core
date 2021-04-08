import logging
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
# python3 -m unittest model.tests.test_FootprintsQuery
# python3 -m unittest model.tests.test_FootprintsQuery.FootprintsQueryTestCase.testAddAoI
#
# evhr102's GDAL version is 2.2.2
# dsg101's GDAL version is 2.1.2
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

        # Axis order for 4326 is backwards.
        env = Envelope()
        env.addPoint(uly, ulx, 0, srs)
        env.addPoint(lry, lrx, 0, srs)

        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        fpq.addAoI(env)
        numScenes = 27
        fpq.setMaximumScenes(numScenes)
        fpScenes1 = fpq.getScenes()
        fpScenes2 = fpq.getScenes()

        self.assertEqual(len(fpScenes1), numScenes)
        self.assertEqual(len(fpScenes1), len(fpScenes2))

        for i in range(len(fpScenes1)):
            self.assertEqual(fpScenes1[i], fpScenes2[i])

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

            dg = DgFile(ntfPath)
            self.assertEqual(dg.specTypeCode(), 'SWIR')

    # -------------------------------------------------------------------------
    # testWithDgFiles
    # -------------------------------------------------------------------------
    def testWithDgFiles(self):

        fpq = FootprintsQuery(FootprintsQueryTestCase._logger)
        fpq.setMaximumScenes(1)
        fpScenes1 = fpq.getScenes()

        for ntfPath in fpScenes1:

            dg = DgFile(ntfPath)
            dg.year()
            dg.fileName()