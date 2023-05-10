#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import math
import shutil
import tempfile
import warnings

from osgeo import gdal
from osgeo.osr import SpatialReference

from core.model.Envelope import Envelope
from core.model.ImageFile import ImageFile
from core.model.SystemCommand import SystemCommand


# -----------------------------------------------------------------------------
# class GeospatialImageFile
#
# The error
# "ERROR 1: netcdf error #-42 : NetCDF: String match to name in use" is 
# described here https://github.com/Unidata/netcdf4-python/issues/1020.
# -----------------------------------------------------------------------------
class GeospatialImageFile(ImageFile):

    FILE_KEY = 'PathToFile'
    SUBDATASET_KEY = 'subdataset'
    LOGGER_KEY = 'logger'
    SRS_KEY = 'SpatialReference'

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, 
                 pathToFile, 
                 spatialReference=None,
                 subdataset=None, 
                 logger=None, 
                 outputFormat='GTiff'):

        # Initialize the base class.
        super(GeospatialImageFile, self).__init__(pathToFile, subdataset)

        self.logger = logger
        self._outputFormat = outputFormat

        # The passed SRS overrides any internal SRS.
        if spatialReference and spatialReference.Validate() == 0:

            self._dataset.SetSpatialRef(spatialReference)

        # Does the image file have a valid SRS?
        if self._dataset.GetSpatialRef() and \
           self._dataset.GetSpatialRef().Validate() == 0:

            return

        # Can the image file's projection be used as an SRS?
        wkt = self.getDataset().GetProjection()

        if wkt:

            projSRS = SpatialReference()
            projSRS.ImportFromWkt(wkt)

            if projSRS.Validate() == 0:
                self._dataset.SetSpatialRef(projSRS)

        # # If there is still no SRS in the image, try to use the one passed.
        # if not self._dataset.GetSpatialRef() or \
        #     self._dataset.GetSpatialRef().Validate() != 0:
        #
        #     if spatialReference and spatialReference.Validate() == 0:
        #         self._dataset.SetSpatialRef(spatialReference)

        # After all that, is there a valid SRS in the image?
        if not self._dataset.GetSpatialRef() or \
           self._dataset.GetSpatialRef().Validate() != 0:

            raise RuntimeError('Spatial reference for ' +
                               pathToFile,
                               ' is invalid.')
                               
    # -------------------------------------------------------------------------
    # clipReproject
    # -------------------------------------------------------------------------
    def clipReproject(self, 
                      envelope=None, 
                      outputSRS=None, 
                      dataset=None,
                      xScale=None,
                      yScale=None):

        # At least one operation must be configured.
        if not envelope and not outputSRS and not xScale and not yScale:

            raise RuntimeError('Clip envelope, output SRS or scale must be ' +
                               'specified.')

        # ---
        # Clip?
        # ---
        obValue = None
        obSRS = None
        destSRS = None
        
        if envelope:

            if not isinstance(envelope, Envelope):
                raise TypeError('The first parameter must be an Envelope.')

            if not self.envelope().Intersection(envelope):

                raise RuntimeError('The clip envelope does not intersect ' +
                                   'the image.')

            obValue = (envelope.ulx(), envelope.lry(), 
                       envelope.lrx(), envelope.uly())
                       
            obSRS = envelope.GetSpatialReference().ExportToProj4()
            
        # ---
        # Reproject?
        # ---
        if outputSRS and not self._dataset.GetSpatialRef().IsSame(outputSRS):
            destSRS = outputSRS.ExportToProj4()
            
        # ---
        # Build the warp options.
        # ---
        options = gdal.WarpOptions(\
            multithread=True,
            format=self._outputFormat,
            srcSRS=self._dataset.GetSpatialRef().ExportToProj4(),
            outputBounds=obValue,
            outputBoundsSRS=obSRS,
            dstSRS=destSRS,
            xRes=xScale,
            yRes=yScale
        )

        # ---
        # Warp
        # ---
        outFile = tempfile.mkstemp()[1]
        dataset = dataset or self._filePath
        gdal.Warp(outFile, dataset, options=options)
        shutil.move(outFile, self._filePath)

        # ---
        # Update the dataset.  It would be nice to use the SRS inside the
        # reprojected file; however, if it is EPSG:4326, the axis order could
        # be incorrect.  Passing the requested SRS keeps the axis order
        # consistent.
        #
        # Is this still relevant?
        # ---
        self.__init__(self._filePath)  #, spatialReference=outputSRS)

    # -------------------------------------------------------------------------
    # clipReprojectOrig
    #
    # These  operations, clipping and reprojection can be combined into a
    # single GDAL call.  This must be more efficient than invoking them
    # individually.
    # -------------------------------------------------------------------------
    # def clipReprojectOrig(self, envelope=None, outputSRS=None, dataset=None):
    #
    #     dataset = dataset or self._filePath
    #
    #     # At least one operation must be configured.
    #     if not envelope and not outputSRS:
    #
    #         raise RuntimeError('Clip envelope or output SRS must be ' +
    #                            'specified.')
    #
    #     cmd = self._getBaseCmd()
    #
    #     # Clip?
    #     if envelope:
    #
    #         if not isinstance(envelope, Envelope):
    #             raise TypeError('The first parameter must be an Envelope.')
    #
    #         if not self.envelope().Intersection(envelope):
    #
    #             raise RuntimeError('The clip envelope does not intersect ' +
    #                                'the image.')
    #
    #         cmd += (' -te' +
    #                 ' ' + str(envelope.ulx()) +
    #                 ' ' + str(envelope.lry()) +
    #                 ' ' + str(envelope.lrx()) +
    #                 ' ' + str(envelope.uly()) +
    #                 ' -te_srs' +
    #                 ' "' + envelope.GetSpatialReference().ExportToProj4() +
    #                 '"')
    #
    #     # Reproject?
    #     if outputSRS and not self._dataset.GetSpatialRef().IsSame(outputSRS):
    #
    #         cmd += ' -t_srs "' + outputSRS.ExportToProj4() + '"'
    #         self._srs = outputSRS
    #
    #     # Finish the command.
    #     outFile = tempfile.mkstemp()[1]
    #     cmd += ' ' + dataset + ' ' + outFile
    #     SystemCommand(cmd, self.logger, True)
    #
    #     shutil.move(outFile, self._filePath)
    #
    #     # ---
    #     # Update the dataset.  It would be nice to use the SRS inside the
    #     # reprojected file; however, if it is EPSG:4326, the axis order could
    #     # be incorrect.  Passing the requested SRS keeps the axis order
    #     # consistent.
    #     # ---
    #     self.__init__(self._filePath, spatialReference=outputSRS)

    # -------------------------------------------------------------------------
    # envelope
    # -------------------------------------------------------------------------
    def envelope(self):

        dataset = self.getDataset()
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

        # ---
        # If this file is in 4326, we must swap the x-y to conform with GDAL
        # 3's strict conformity to the 4326 definition.
        # ---
        srs4326 = SpatialReference()
        srs4326.ImportFromEPSG(4326)

        if srs4326.IsSame(self._dataset.GetSpatialRef()):

            envelope.addPoint(uly, ulx, 0, self._dataset.GetSpatialRef())
            envelope.addPoint(lry, lrx, 0, self._dataset.GetSpatialRef())

        else:

            envelope.addPoint(ulx, uly, 0, self._dataset.GetSpatialRef())
            envelope.addPoint(lrx, lry, 0, self._dataset.GetSpatialRef())

        return envelope

    # -------------------------------------------------------------------------
    # _getBaseCmd
    # -------------------------------------------------------------------------
    def _getBaseCmd(self):

        return 'gdalwarp ' + \
               ' -multi' + \
               ' -of ' + str(self._outputFormat) + \
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
    # def resample(self, xScale, yScale):
    #
    #     cmd = self._getBaseCmd() + ' -tr ' + str(xScale) + ' ' + \
    #         str(yScale)
    #
    #     # Finish the command.
    #     outFile = tempfile.mkstemp(suffix='.nc')[1]
    #     cmd += ' ' + self._filePath + ' ' + outFile
    #     SystemCommand(cmd, None, True)
    #     shutil.move(outFile, self._filePath)
    #
    #     # Update the dataset.
    #     self.getDataset()

    # -------------------------------------------------------------------------
    # resample
    # -------------------------------------------------------------------------
    def resample(self, xScale, yScale):

        warnings.warn('Use osgeo.gdal.Warp, instead.', 
                      DeprecationWarning,
                      stacklevel=2)
                      
        self.clipReproject(xScale=xScale, yScale=yScale)
        
    # -------------------------------------------------------------------------
    # scale
    # -------------------------------------------------------------------------
    def scale(self):

        xform = self.getDataset().GetGeoTransform()
        return xform[1], xform[5]

    # -------------------------------------------------------------------------
    # srs
    # -------------------------------------------------------------------------
    def srs(self):

        return self._dataset.GetSpatialRef()

    # -------------------------------------------------------------------------
    # subdataset
    # -------------------------------------------------------------------------
    def subdataset(self):
        return self._subdataset

    # -------------------------------------------------------------------------
    # __getstate__
    # -------------------------------------------------------------------------
    def __getstate__(self):

        state = {GeospatialImageFile.FILE_KEY: self.fileName(),
                 GeospatialImageFile.SRS_KEY: self.srs().ExportToProj4(),
                 GeospatialImageFile.SUBDATASET_KEY: self.subdataset(),
                 GeospatialImageFile.LOGGER_KEY: self.logger}

        return state

    # -------------------------------------------------------------------------
    # __setstate__
    #
    # e2 = pickle.loads(pickle.dumps(env))
    # -------------------------------------------------------------------------
    def __setstate__(self, state):

        srs = SpatialReference()
        srs.ImportFromProj4(state[GeospatialImageFile.SRS_KEY])

        self.__init__(state[GeospatialImageFile.FILE_KEY],
                      srs,
                      state[GeospatialImageFile.SUBDATASET_KEY],
                      state[GeospatialImageFile.LOGGER_KEY])
