#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import struct

import numpy as np

from osgeo import gdalconst

from core.model.ImageFile import ImageFile


# -----------------------------------------------------------------------------
# class Chunker
#
# This works on GDAL image files, so GDAL can perform the partial reads from
# the raster.  The alternative would be to read an entire image into an array.
# While this would allow a Chunker to be created from a chunk of another
# Chunker, it is probably not worth the memory consumption.
# -----------------------------------------------------------------------------
class Chunker(object):

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, imageFileName):

        self._imageFile = ImageFile(imageFileName)
        self._xSize = 1
        self._ySize = 1
        self._curChunkLoc = (0, 0)
        self._complete = False

    # -------------------------------------------------------------------------
    # getChunk
    #
    # The parameters xStart and yStart allow users to override the chunking
    # process.  This can be helpful when distributing image reads via Celery
    # because GDAL datasets cannot be serialized with Pickle.  In these cases,
    # the controlling process can use chunker to step through the image without
    # reading, just returning the location of each chunk.  These chunk
    # locations can be passed to a distributed process, along with the image
    # path, to create another chunker.  That chunker can pass the chunk
    # location to getChunk(), instead of calling GDAL directly.  The benefit is
    # that getChunk() manages the ends of rows and columns, and transposes the
    # buffer so that it is in (x, y) orientation.
    #
    # This might be easier to understand as a specialized Chunker class because
    # this version crams two slightly different uses into one.  Trying to keep
    # it simple, with one class.
    # -------------------------------------------------------------------------
    def getChunk(self, xStart=None, yStart=None, read=True):

        if self._complete:
            return (None, None)

        if not self._xSize:
            raise RuntimeError('The chunk x size must be set.')

        if not self._ySize:
            raise RuntimeError('The chunk y size must be set.')

        xStart = xStart or self._curChunkLoc[0]
        yStart = yStart or self._curChunkLoc[1]
        xLen = self._xSize
        yLen = self._ySize
        next_xStart = xStart + xLen
        next_yStart = yStart
        xExceeded = False
        yExceeded = False

        # X dimension exceeded?
        if xStart + xLen > self._imageFile._getDataset().RasterXSize:

            # Limit the read in the X dimension.
            xLen = self._imageFile._getDataset().RasterXSize - xStart

            # If the length is 0, move to the next chunk row now.
            if xLen == 0:

                xStart = 0
                yStart = yStart + self._ySize
                xLen = self._xSize
                next_xStart = xStart + xLen
                next_yStart = yStart

            else:

                # Move to next chunk row for the following chunk.
                next_xStart = 0
                next_yStart = yStart + self._ySize

            # When X and Y are exceeded, chunking is complete.
            xExceeded = True

        # Y dimension exceeded?  Must be the last row of the image.
        if yStart + yLen > self._imageFile._getDataset().RasterYSize:

            # Limit the read in the Y dimension.
            yLen = self._imageFile._getDataset().RasterYSize - yStart

            # ---
            # When yLen is 0, the next read cannot happen.  If yLen is not 0,
            # read the final portion of a chunk below.
            # ---
            if yLen == 0:
                self._complete = True

            # Last row, so Y start stays the same.
            next_yStart = yStart

            # When X and Y are exceeded, chunking is complete.
            yExceeded = True

        if not self.isComplete() and read:

            rcChunk = self._imageFile._getDataset().ReadAsArray(xStart,
                                                                yStart,
                                                                xLen,
                                                                yLen)

            # Load the chunk as (x, y), instead of (row, column).
            chunk = rcChunk.transpose()

        else:

            chunk = np.empty([0, 0])

        # When X and Y are exceeded, chunking is complete.
        if xExceeded and yExceeded:
            self._complete = True

        # Set position of next chunk.
        self._curChunkLoc = (next_xStart, next_yStart)

        return ((xStart, yStart), chunk)

    # -------------------------------------------------------------------------
    # isComplete
    # -------------------------------------------------------------------------
    def isComplete(self):
        return self._complete

    # -------------------------------------------------------------------------
    # reset
    # -------------------------------------------------------------------------
    def reset(self):

        self._curChunkLoc = (0, 0)
        self._complete = False

    # -------------------------------------------------------------------------
    # setChunkAsColumn
    # -------------------------------------------------------------------------
    def setChunkAsColumn(self):

        self.setChunkSize(1, self._imageFile._getDataset().RasterYSize)

    # -------------------------------------------------------------------------
    # setChunkAsRow
    # -------------------------------------------------------------------------
    def setChunkAsRow(self):

        self.setChunkSize(self._imageFile._getDataset().RasterXSize, 1)

    # -------------------------------------------------------------------------
    # setChunkToImage
    # -------------------------------------------------------------------------
    def setChunkToImage(self):

        self.setChunkSize(self._imageFile._getDataset().RasterXSize,
                          self._imageFile._getDataset().RasterYSize)

    # -------------------------------------------------------------------------
    # setChunkSize
    # -------------------------------------------------------------------------
    def setChunkSize(self, _xSize, _ySize):

        if _xSize < 1:
            raise RuntimeError('The sample size of a chunk must be greater ' +
                               'than zero.')

        if _xSize > self._imageFile._getDataset().RasterXSize:

            raise RuntimeError('Sample size, ' +
                               str(_xSize) +
                               ', must be less than or equal to the image ' +
                               'sample size, ' +
                               str(self._imageFile._getDataset().RasterXSize))

        if _ySize < 1:
            raise RuntimeError('The line size of a chunk must be greater ' +
                               'than zero.')

        if _ySize > self._imageFile._getDataset().RasterYSize:

            raise RuntimeError('Line size, ' +
                               str(_ySize) +
                               ', must be less than or equal to the image ' +
                               'line size, ' +
                               str(self._imageFile._getDataset().RasterYSize))

        self._xSize = _xSize
        self._ySize = _ySize
