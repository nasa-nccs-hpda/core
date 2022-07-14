
import os
import unittest
from xml.dom import minidom

from core.model.FootprintsScene import FootprintsScene


# ------------------------------------------------------------------------------
# FootprintsSceneTestCase
#
# python -m unittest discover core/model/tests/
# python -m unittest core.model.tests.test_FootprintsScene
# ------------------------------------------------------------------------------
class FootprintsSceneTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # testFootprintsScene
    # -------------------------------------------------------------------------
    def testFootprintsScene(self):

        GML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'scene.gml')

        sceneGML = minidom.parse(GML_FILE)
        print('type = ', type(sceneGML))
        features = sceneGML.getElementsByTagName('gml:featureMember')[0]
        fps = FootprintsScene(sceneGML=features)

        self.assertEqual(fps.fileName(),
                         '/css/nga/WV01/1B/2015/100/' +
                         'WV01_102001003A7E9A00_X1BS_502788423060_01/' +
                         'WV01_20150410052955_102001003A7E9A00_' +
                         '15APR10052955-P1BS-502788423060_01_P005.ntf')

        self.assertEqual(fps.pairName(),
                         'WV01_20150410_102001003C718E00_102001003A7E9A00')

        self.assertEqual(fps.stripName(),
                         'WV01_102001003A7E9A00_P1BS_502788423060_01')

        # Test retrieving a tag that does not exist.
        with self.assertRaises(RuntimeError):
            fps._getValue(sceneGML, 'doesNotExist')

        # Test retrieving a null tag.
        self.assertIsNone(fps._getValue(sceneGML, 'ogr:avtargetaz'))

    # -------------------------------------------------------------------------
    # testSorting
    #
    # This is to reproduce a client's run-time error and demonstrate that is
    # is fixed.
    # -------------------------------------------------------------------------
    def testSorting(self):

        print('In testSorting ...')

        GML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'scene.gml')

        sceneGML = minidom.parse(GML_FILE)
        features = sceneGML.getElementsByTagName('gml:featureMember')[0]
        fps = FootprintsScene(sceneGML=features)

        GML_FILE2 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'scene2.gml')

        scene2GML = minidom.parse(GML_FILE2)
        features2 = sceneGML.getElementsByTagName('gml:featureMember')[0]
        fps2 = FootprintsScene(sceneGML=features2)

        sceneList = [fps, fps2]
        sceneList.sort()

    # -------------------------------------------------------------------------
    # testPgRecord
    # -------------------------------------------------------------------------
    def testPgRecord(self):

        file1 = '/css/nga/WV01/1B/2022/121/' + \
                'WV01_10200100C37ECB00_P1BS_506406585010_01/' + \
                'WV01_20220501072725_10200100C37ECB00_22MAY01072725' + \
                '-P1BS-506406585010_01_P007.ntf'

        strip1 = 'WV01_10200100C37ECB00_P1BS_506406585010_01'
        fps1 = FootprintsScene(pgRecord=(file1, None, strip1))
        self.assertEqual(file1, fps1.fileName())
        self.assertEqual(None, fps1.pairName())
        self.assertEqual(strip1, fps1.stripName())
