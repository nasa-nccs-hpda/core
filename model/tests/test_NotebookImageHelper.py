import numpy as np
from osgeo import gdal
import unittest

from core.model.NotebookImageHelper import NotebookImageHelper


class NotebookImageHelperTests(unittest.TestCase):

    def setUp(self):

        # Create dummy numpy arrays for RGB bands
        width = 100
        height = 100

        red_band = np.zeros((height, width), dtype=np.uint8)
        green_band = np.ones((height, width), dtype=np.uint8)
        blue_band = np.full((height, width), 255, dtype=np.uint8)

        # Create an in-memory dataset
        driver = gdal.GetDriverByName('MEM')

        dataset = driver.Create('', width, height, 3, gdal.GDT_Byte)

        dataset.GetRasterBand(1).WriteArray(red_band)
        dataset.GetRasterBand(2).WriteArray(green_band)
        dataset.GetRasterBand(3).WriteArray(blue_band)

        self.dataset = dataset

        self.noDataValue = -9999.0

        self.redBandId = 1
        self.greenBandId = 2
        self.blueBandId = 3

        self.helper = NotebookImageHelper()

        self.helper.initFromDataset(
            self.dataset,
            self.noDataValue,
            self.redBandId,
            self.greenBandId,
            self.blueBandId
        )

    def tearDown(self):

        self.dataset = None

        self.helper = None

    def test_initFromDataset(self):

        self.assertEqual(self.helper._dataset, self.dataset)

        self.assertEqual(self.helper._noDataValue, self.noDataValue)

        self.assertEqual(self.helper._redBandId, self.redBandId)

        self.assertEqual(self.helper._greenBandId, self.greenBandId)

        self.assertEqual(self.helper._blueBandId, self.blueBandId)

        self.assertIsNotNone(self.helper._redBand)

        self.assertIsNotNone(self.helper._greenBand)

        self.assertIsNotNone(self.helper._blueBand)

        self.assertEqual(self.helper._minValue, np.min(self.helper._redBand))

        self.assertEqual(self.helper._maxValue, np.max(self.helper._redBand))

    def test_getCorners(self):

        corners = self.helper.getCorners()

        self.assertIsInstance(corners, tuple)

        self.assertEqual(len(corners), 4)

    def test_getRgbIndexList(self):

        rgbIndexList = self.helper.getRgbIndexList()

        self.assertIsInstance(rgbIndexList, list)

        self.assertEqual(len(rgbIndexList), 3)

    def test_getRgbBands(self):

        rgbBands = self.helper.getRgbBands()

        self.assertIsInstance(rgbBands, list)

        self.assertEqual(len(rgbBands), 3)

    def test_str(self):

        string = str(self.helper)

        expectedString = 'Input file: ' + str(None) + \
            '\nMin. pixel: ' + str(0) + \
            '\nMax. pixel: ' + str(0) + \
            '\nNo-data value: ' + str(-9999.0) + \
            '\nRed band index: ' + str(1) + \
            '\nGreen band index: ' + str(2) + \
            '\nBlue band index: ' + str(3) + \
            '\nCorners: ' + str((0.0, 100.0, 100.0, 0.0))

        self.assertEqual(string, expectedString)
