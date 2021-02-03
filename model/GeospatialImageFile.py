#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import math
import os
import shutil
import tempfile

from osgeo.osr import SpatialReference

from core.model.Envelope import Envelope
from core.model.ImageFile import ImageFile
from core.model.SystemCommand import SystemCommand


# -----------------------------------------------------------------------------
# class GeospatialImageFile
# -----------------------------------------------------------------------------
class GeospatialImageFile(ImageFile):

    FILE_KEY = 'PathToFile'
    SRS_KEY = 'SpatialReference'

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, pathToFile, spatialReference=None, logger=None):

        # Initialize the base class.
        super(GeospatialImageFile, self).__init__(pathToFile)

        self.logger = logger

        # Initialize the spatial reference.
        if not spatialReference:

            spatialReferenceWkt = self._getDataset().GetProjection()
            spatialReference = SpatialReference()
            spatialReference.ImportFromWkt(spatialReferenceWkt)

        if spatialReference.Validate() != 0:

            raise RuntimeError('Spatial reference for ' +
                               pathToFile,
                               ' is invalid.')

        self._dataset.SetSpatialRef(spatialReference)

    # -------------------------------------------------------------------------
    # clipReproject
    #
    # These  operations, clipping and reprojection can be combined into a
    # single GDAL call.  This must be more efficient than invoking them
    # individually.
    # -------------------------------------------------------------------------
    def clipReproject(self, envelope=None, outputSRS=None, dataset=None):

        dataset = dataset or self._filePath

        # At least one operation must be configured.
        if not envelope and not outputSRS:

            raise RuntimeError('Clip envelope or output SRS must be ' +
                               'specified.')

        cmd = self._getBaseCmd()

        # Clip?
        if envelope:

            if not isinstance(envelope, Envelope):
                raise TypeError('The first parameter must be an Envelope.')

            if not self.envelope().Intersection(envelope):

                raise RuntimeError('The clip envelope does not intersect ' +
                                   'the image.')

            cmd += (' -te' +
                    ' ' + str(envelope.ulx()) +
                    ' ' + str(envelope.lry()) +
                    ' ' + str(envelope.lrx()) +
                    ' ' + str(envelope.uly()) +
                    ' -te_srs' +
                    ' "' + envelope.GetSpatialReference().ExportToProj4() +
                    '"')

        # Reproject?
        if outputSRS and not self._dataset.GetSpatialRef().IsSame(outputSRS):

            cmd += ' -t_srs "' + outputSRS.ExportToProj4() + '"'
            self._srs = outputSRS

        # Finish the command.
        outFile = tempfile.mkstemp()[1]
        cmd += ' ' + dataset + ' ' + outFile
        SystemCommand(cmd, self.logger, True)

        shutil.move(outFile, self._filePath)

        # Update the dataset.
        self.__init__(self._filePath, outputSRS)

    # -------------------------------------------------------------------------
    # envelope
    # -------------------------------------------------------------------------
    def envelope(self):

        dataset = self._getDataset()
        xform = dataset.GetGeoTransform()
        xScale = xform[1]
        yScale = xform[5]
        width = dataset.RasterXSize
        height = dataset.RasterYSize
        ulx = xform[0]
        uly = xform[3]
        lrx = ulx + width * xScale
        lry = uly + height * yScale

        envelope = Envelope()
        envelope.addPoint(ulx, uly, 0, self._dataset.GetSpatialRef())
        envelope.addPoint(lrx, lry, 0, self._dataset.GetSpatialRef())

        return envelope

    # -------------------------------------------------------------------------
    # _getBaseCmd
    # -------------------------------------------------------------------------
    def _getBaseCmd(self):

        return 'gdalwarp ' + \
               ' -multi' + \
               ' -of netCDF' + \
               ' -s_srs "' + \
               self._dataset.GetSpatialRef().ExportToProj4() + \
               '"'

    # -------------------------------------------------------------------------
    # getSquareScale
    #
    # Some ASCII image variants cannot represent pixel size in two dimensions.
    # When an ASCII image with rectangular pixels is represented with a
    # single-dimension variant, it introduces a ground shift.  This method
    # returns a single value suitable for resampling the pixels to be square.
    # The image must be resampled using this value.
    # -------------------------------------------------------------------------
    def getSquareScale(self):

        xScale = self.scale()[0]
        yScale = self.scale()[1]

        if math.fabs(xScale) > math.fabs(yScale):
            return math.fabs(xScale * -1)  # xScale bigger, so increase yScale

        return math.fabs(yScale * -1)

    # -------------------------------------------------------------------------
    # resample
    # -------------------------------------------------------------------------
    def resample(self, xScale, yScale):

        cmd = self._getBaseCmd() + ' -tr ' + str(xScale) + ' ' + \
              str(yScale)

        # Finish the command.
        outFile = tempfile.mkstemp(suffix='.nc')[1]
        cmd += ' ' + self._filePath + ' ' + outFile
        SystemCommand(cmd, None, True)
        shutil.move(outFile, self._filePath)

        # Update the dataset.
        self._getDataset()

    # -------------------------------------------------------------------------
    # scale
    # -------------------------------------------------------------------------
    def scale(self):

        xform = self._getDataset().GetGeoTransform()
        return xform[1], xform[5]

    # -------------------------------------------------------------------------
    # srs
    # -------------------------------------------------------------------------
    def srs(self):

        return self._dataset.GetSpatialRef()

    # -------------------------------------------------------------------------
    # __getstate__
    # -------------------------------------------------------------------------
    def __getstate__(self):

        state = {GeospatialImageFile.FILE_KEY: self.fileName(),
                 GeospatialImageFile.SRS_KEY: self.srs().ExportToProj4()}

        return state

    # -------------------------------------------------------------------------
    # __setstate__
    #
    # e2 = pickle.loads(pickle.dumps(env))
    # -------------------------------------------------------------------------
    def __setstate__(self, state):

        srs = SpatialReference()
        srs.ImportFromProj4(state[GeospatialImageFile.SRS_KEY])
        self.__init__(state[GeospatialImageFile.FILE_KEY], srs)
