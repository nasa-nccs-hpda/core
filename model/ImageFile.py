#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from osgeo import gdal
from osgeo import gdalconst

from core.model.BaseFile import BaseFile


# -----------------------------------------------------------------------------
# class ImageFile
#
# This class represents our single image format, NetCDF.
# -----------------------------------------------------------------------------
class ImageFile(BaseFile):

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, pathToFile, readOnly=True):

        # Initialize the base class.
        super(ImageFile, self).__init__(pathToFile)

        # ---
        # Corrupt files tend to fail when they are opened in _getDataset(),
        # so try it here and fail early.
        # ---
        self._dataset = None

        try:
            ro = gdalconst.GA_ReadOnly if readOnly else gdalconst.GF_Write
            self._dataset = gdal.Open(self._filePath, ro)

            if not self._dataset:

                raise RuntimeError('GDAL returned an null data set ' +
                                   'when opening ' +
                                   self._filePath +
                                   '.')

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            raise RuntimeError('GDAL raised an exception when opening ' +
                               self._filePath + '.')

    # -------------------------------------------------------------------------
    # _getDataset
    # -------------------------------------------------------------------------
    def _getDataset(self):

        return self._dataset
