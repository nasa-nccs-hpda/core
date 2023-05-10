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
    def __init__(self, pathToFile, subdataset=None, readOnly=True):

        # Initialize the base class.
        super(ImageFile, self).__init__(pathToFile)

        # ---
        # Corrupt files tend to fail when they are opened in _getDataset(),
        # so try it here and fail early.
        # ---
        self._dataset = None
        self._subdataset = subdataset

        try:
            ro = gdalconst.GA_ReadOnly if readOnly else gdalconst.GF_Write
            
            self._dataset = gdal.Open(subdataset, ro) \
                if subdataset else gdal.Open(pathToFile, ro)

            if not self._dataset:

                raise RuntimeError('GDAL returned an null data set ' +
                                   'when opening ' +
                                   self._filePath +
                                   '.')

        except Exception:

            raise RuntimeError('GDAL raised an exception when opening ' +
                               self._filePath + '.')

    # -------------------------------------------------------------------------
    # getDataset
    # -------------------------------------------------------------------------
    def getDataset(self):

        return self._dataset
