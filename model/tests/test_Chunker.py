#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import unittest

import numpy as np

from core.model.Chunker import Chunker


# -----------------------------------------------------------------------------
# class ChunkerTestCase
#
# python -m unittest discover model/tests/
# python -m unittest core.model.tests.test_Chunker
# -----------------------------------------------------------------------------
class ChunkerTestCase(unittest.TestCase):

    # -------------------------------------------------------------------------
    # testInit
    # -------------------------------------------------------------------------
    def testInit(self):

        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        Chunker(testFile)

    # -------------------------------------------------------------------------
    # testNoRead
    # -------------------------------------------------------------------------
    def testNoRead(self):

        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)
        c.setChunkAsColumn()
        loc, chunk = c.getChunk(None, None, False)
        self.assertEqual(loc, (0, 0))
        self.assertEqual(chunk.size, 0)

    # -------------------------------------------------------------------------
    # testReadSingleChunk
    # -------------------------------------------------------------------------
    def testReadSingleChunk(self):

        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)
        c.setChunkSize(1, 1)
        loc, chunk = c.getChunk(2, 98)
        self.assertEqual(loc, (2, 98))
        self.assertEqual(chunk[0], 26)

    # -------------------------------------------------------------------------
    # testIsComplete
    # -------------------------------------------------------------------------
    def testIsComplete(self):

        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)

        while not c.isComplete():
            loc, chunk = c.getChunk()

    # -------------------------------------------------------------------------
    # testSetChunkDimensions
    # -------------------------------------------------------------------------
    def testSetChunkDimensions(self):

        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)

        with self.assertRaisesRegex(RuntimeError,
                                    'sample size of a chunk must be greater'):
            c.setChunkSize(-1, 10)

        with self.assertRaisesRegex(RuntimeError,
                                    'Sample size.*must be less'):
            c.setChunkSize(1000000000, 10)

        with self.assertRaisesRegex(RuntimeError,
                                    'line size of a chunk must be greater'):
            c.setChunkSize(10, -1)

        with self.assertRaisesRegex(RuntimeError,
                                    'Line size.*must be less'):
            c.setChunkSize(10, 1000000000)

        c.setChunkSize(10, 15)
        self.assertEqual(c._xSize, 10)
        self.assertEqual(c._ySize, 15)

    # -------------------------------------------------------------------------
    # testSetChunkAsColumn
    # -------------------------------------------------------------------------
    def testSetChunkAsColumn(self):

        # 578 x 464
        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)
        c.setChunkAsColumn()
        self.assertEqual(c._xSize, 1)
        self.assertEqual(c._ySize, 464)
        loc, chunk = c.getChunk()
        self.assertEqual(chunk.shape, (1, 464))

    # -------------------------------------------------------------------------
    # testSetChunkAsRow
    # -------------------------------------------------------------------------
    def testSetChunkAsRow(self):

        # 578 x 464
        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)
        c.setChunkAsRow()
        self.assertEqual(c._xSize, 578)
        self.assertEqual(c._ySize, 1)
        loc, chunk = c.getChunk()
        self.assertEqual(chunk.shape, (578, 1))
        c.reset()

        # ---
        # There was a problem with the second call to getChunk, when chunking
        # by rows.
        # ---
        loc, chunk = c.getChunk()
        self.assertEqual(loc, (0, 0))
        loc, chunk = c.getChunk()
        self.assertEqual(loc, (0, 1))
        self.assertNotEqual(chunk.shape, (0, 1))

        # ---
        # The third iteration caused a problem, too.  These had to do with
        # detecting ends of rows and properly updating the row pointers.
        # ---
        loc, chunk = c.getChunk()
        self.assertEqual(loc, (0, 2))

        # ---
        # Loop through all remaining rows.  Try to access the column each time.
        # This tests that the end of the rows are detected.
        # ---
        loc, chunk = c.getChunk()

        while loc:
            loc, chunk = c.getChunk()

    # -------------------------------------------------------------------------
    # testGetChunkBookkeeping
    # -------------------------------------------------------------------------
    def testGetChunkBookkeeping(self):

        # 578 x 464
        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)
        xSize = 250
        ySize = 200
        c.setChunkSize(xSize, ySize)

        # ---
        # The image is 578 x 464, and it's type is byte.  Check each chunk's
        # progression through the image.
        # ---
        loc, chunk = c.getChunk()
        outBuffer = np.empty([578, 464], dtype=chunk.dtype)
        self.assertEqual(loc[0], 0)
        self.assertEqual(loc[1], 0)
        outBuffer[loc[0]:loc[0]+xSize, loc[1]:loc[1]+ySize] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])

        self.assertEqual(chunk[xSize-1][ySize-1],
                         outBuffer[loc[0] + xSize-1][loc[1] + ySize-1])

        loc, chunk = c.getChunk()
        self.assertEqual(loc[0], xSize)
        self.assertEqual(loc[1], 0)
        outBuffer[loc[0]:loc[0]+xSize, loc[1]:loc[1]+ySize] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])

        self.assertEqual(chunk[xSize-1][ySize-1],
                         outBuffer[loc[0] + xSize-1][loc[1] + ySize-1])

        # This hits the end of the first chunk row.
        loc, chunk = c.getChunk()
        self.assertEqual(loc[0], 500)
        self.assertEqual(loc[1], 0)
        outBuffer[loc[0]:loc[0]+250, loc[1]:loc[1]+200] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])
        self.assertEqual(chunk[77][199], outBuffer[loc[0]+77][loc[1]+199])

        loc, chunk = c.getChunk()
        self.assertEqual(loc[0], 0)
        self.assertEqual(loc[1], 200)
        outBuffer[loc[0]:loc[0]+250, loc[1]:loc[1]+200] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])
        self.assertEqual(chunk[249][199], outBuffer[loc[0]+249][loc[1]+199])

        loc, chunk = c.getChunk()
        self.assertEqual(loc[0], 250)
        self.assertEqual(loc[1], 200)
        outBuffer[loc[0]:loc[0]+250, loc[1]:loc[1]+200] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])
        self.assertEqual(chunk[249][199], outBuffer[loc[0]+249][loc[1]+199])

        # This hits the end of the second chunk row.
        loc, chunk = c.getChunk()
        self.assertEqual(loc[0], 500)
        self.assertEqual(loc[1], 200)
        outBuffer[loc[0]:loc[0]+250, loc[1]:loc[1]+200] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])
        self.assertEqual(chunk[77][199], outBuffer[loc[0]+77][loc[1]+199])

        # This hits the end of the first chunk column.
        loc, chunk = c.getChunk()
        self.assertEqual(loc[0], 0)
        self.assertEqual(loc[1], 400)
        outBuffer[loc[0]:loc[0]+250, loc[1]:loc[1]+200] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])
        self.assertEqual(chunk[249][63], outBuffer[loc[0]+249][loc[1]+63])

        loc, chunk = c.getChunk()
        self.assertEqual(loc[0], 250)
        self.assertEqual(loc[1], 400)
        outBuffer[loc[0]:loc[0]+250, loc[1]:loc[1]+200] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])
        self.assertEqual(chunk[249][63], outBuffer[loc[0]+249][loc[1]+63])

        loc, chunk = c.getChunk()
        self.assertEqual(loc[0], 500)
        self.assertEqual(loc[1], 400)
        outBuffer[loc[0]:loc[0]+250, loc[1]:loc[1]+200] = chunk
        self.assertEqual(chunk[0][0], outBuffer[loc[0]][loc[1]])
        self.assertEqual(chunk[77][63], outBuffer[loc[0]+77][loc[1]+63])

        # Try to read after the last chunk.
        loc, chunk = c.getChunk()
        self.assertIsNone(loc)
        self.assertIsNone(chunk)

    # -------------------------------------------------------------------------
    # testReset
    # -------------------------------------------------------------------------
    def testReset(self):

        # 578 x 464
        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)

        while not c.isComplete():
            c.getChunk()

        c.reset()
        c.getChunk()

    # -------------------------------------------------------------------------
    # testReadAccuracy
    # -------------------------------------------------------------------------
    def testReadAccuracy(self):

        # 578 x 464
        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)
        c.setChunkToImage()

        # ---
        # Use: gdallocationinfo -valonly
        # model/tests/gsenm_250m_eucl_dist_streams.tif x y to get the test
        # values.
        # ---
        loc, chunk = c.getChunk()
        self.assertEqual(chunk[0, 0], 0)        # image(0, 0)
        self.assertEqual(chunk[2, 98], 26)      # image(2, 98)
        self.assertEqual(chunk[21, 12], 9)      # image(21, 12)
        self.assertEqual(chunk[99, 100], 1)     # image(99, 100)
        self.assertEqual(chunk[577, 463], 101)  # image(577, 463)

    # -------------------------------------------------------------------------
    # testSetChunkToImage
    # -------------------------------------------------------------------------
    def testSetChunkToImage(self):

        # 578 x 464
        testFile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gsenm_250m_eucl_dist_streams.tif')

        c = Chunker(testFile)
        c.setChunkToImage()
        loc, chunk = c.getChunk()
        self.assertEqual(loc, (0, 0))
        self.assertEqual(chunk.shape, (578, 464))

    # -------------------------------------------------------------------------
    # testMultipleBands
    # -------------------------------------------------------------------------
    def testMultipleBands(self):

        # Image is 653 x 7074 x 425
        testFile = '/css/above/daac.ornl.gov/daacdata/above/' + \
                   'ABoVE_Airborne_AVIRIS_NG/data/' + \
                   'ang20180729t210144rfl/ang20180729t210144_rfl_v2r2/' + \
                   'ang20180729t210144_corr_v2r2_img'

        c = Chunker(testFile)
        c.setChunkSize(50, 75)
        loc, chunk = c.getChunk()
        self.assertEqual(chunk.shape, (50, 75, 425))

        # ---
        # Band numbering starts at 1 in gdal and it starts at 0 here, so
        # the band number is 1 less in the chunk reference.
        # Use the following command to verify chunk values.
        #
        # gdallocationinfo -valonly /att/pubrepo/ABoVE/archived_data/ORNL/ABoVE_Airborne_AVIRIS_NG_CORRUPT/data/ang20180729t210144rfl/ang20180729t210144_rfl_v2r2/ang20180729t210144_corr_v2r2_img 40 70 -b 80
        # ---
        self.assertAlmostEqual(chunk[40, 70, 79], 0.258098900318146, 7)

        loc, chunk = c.getChunk()
        self.assertAlmostEqual(chunk[0, 70, 0], 0.0045041959, 7)  # 50, 70, 1
