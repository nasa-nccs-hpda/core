#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from osgeo import ogr
from osgeo import osr
from osgeo.osr import CoordinateTransformation
from osgeo.osr import SpatialReference


# -----------------------------------------------------------------------------
# class Envelope
# -----------------------------------------------------------------------------
class Envelope(ogr.Geometry):

    MULTIPOINT_KEY = 'Multipoint'
    SRS_KEY = 'SpatialReference'

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self):

        # Initialize the base class.
        super(Envelope, self).__init__(ogr.wkbMultiPoint)

        # ---
        # Hang onto EPSG:4326 because it is a special case that must be
        # accommodated in various places.
        # ---
        self._srs4326 = SpatialReference()
        self._srs4326.ImportFromEPSG(4326)

    # -------------------------------------------------------------------------
    # addPoint
    #
    # NOTE:  The underlying GDAL OGR Geometry class is unable to detect invalid
    # ordinates.  For example, it is possible to set a latitude to 91.  As
    # these values are relative to a point's SRS, it is difficult to check each
    # case.  A Point class would help, but could lead to extensive wrapping of
    # GDAL, which we should avoid--or at least strongly resist.
    # -------------------------------------------------------------------------
    def addPoint(self, x, y, z, srs):

        ogrPt = ogr.Geometry(ogr.wkbPoint)
        ogrPt.AssignSpatialReference(srs)

        # ---
        # The next line causes the GetGeometryType() to become -2147483647,
        # although GetGeometryName() remains 'POINT'.
        # ---
        ogrPt.AddPoint(x, y, z)

        self.addOgrPoint(ogrPt)

    # -------------------------------------------------------------------------
    # addOgrPoint
    # -------------------------------------------------------------------------
    def addOgrPoint(self, ogrPoint):

        # GetGeometryType() is sometimes corrupt, so check it's name, too.
        if ogrPoint.GetGeometryType() != ogr.wkbPoint and \
           ogrPoint.GetGeometryName() != 'POINT':

            raise RuntimeError('Added points must be of type wkbPoint.')

        if not self.GetSpatialReference():

            self.AssignSpatialReference(
                ogrPoint.GetSpatialReference().Clone())

        if not ogrPoint.GetSpatialReference(). \
           IsSame(self.GetSpatialReference()):

            raise RuntimeError('Added points must be in the SRS: ' +
                               str(self.GetSpatialReference().
                                   ExportToPrettyWkt()))

        self.AddGeometry(ogrPoint)

    # -------------------------------------------------------------------------
    # Equals
    #
    # NOTE:  Overriding Geometry's Equals method to specialize its behavior
    # for envelopes.
    # -------------------------------------------------------------------------
    def Equals(self, otherEnvelope):

        return self.ulx() == otherEnvelope.ulx() and \
               self.uly() == otherEnvelope.uly() and \
               self.lrx() == otherEnvelope.lrx() and \
               self.lry() == otherEnvelope.lry() and \
               self.GetSpatialReference().IsSame(
                   otherEnvelope.GetSpatialReference())

    # -------------------------------------------------------------------------
    # expandByPercentage
    # -------------------------------------------------------------------------
    def expandByPercentage(self, percentage=10):

        ulPoint = ogr.Geometry(ogr.wkbPoint)
        ulPoint.AddPoint(float(self.ulx()), float(self.uly()))
        ulPoint.AssignSpatialReference(self.GetSpatialReference())

        lrPoint = ogr.Geometry(ogr.wkbPoint)
        lrPoint.AddPoint(float(self.lrx()), float(self.lry()))
        lrPoint.AssignSpatialReference(self.GetSpatialReference())

        urPoint = ogr.Geometry(ogr.wkbPoint)
        urPoint.AddPoint(float(self.lrx()), float(self.uly()))
        urPoint.AssignSpatialReference(self.GetSpatialReference())

        width = ulPoint.Distance(urPoint)
        height = ulPoint.Distance(lrPoint)

        pct = percentage / 100.0
        exWidth = abs(width * pct / 2.0)
        exHeight = abs(height * pct / 2.0)

        exUlx = self.ulx() - exWidth
        exUly = self.uly() + exHeight
        exLrx = self.lrx() + exWidth
        exLry = self.lry() - exHeight

        return exUlx, exUly, exLrx, exLry

    # -------------------------------------------------------------------------
    # lrx
    # -------------------------------------------------------------------------
    def lrx(self):

        # if self.GetSpatialReference().IsSame(self._srs4326):
        #
        #     return self.GetEnvelope()[3]
        #
        # else:

        if self.GetSpatialReference().IsSame(self._srs4326):
            self.GetSpatialReference(). \
                SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        return self.GetEnvelope()[1]

    # -------------------------------------------------------------------------
    # lry
    # -------------------------------------------------------------------------
    def lry(self):

        # if self.GetSpatialReference().IsSame(self._srs4326):
        #
        #     return self.GetEnvelope()[0]
        #
        # else:

        if self.GetSpatialReference().IsSame(self._srs4326):
            self.GetSpatialReference(). \
                SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        return self.GetEnvelope()[2]

    # -------------------------------------------------------------------------
    # ulx
    # -------------------------------------------------------------------------
    def ulx(self):

        # if self.GetSpatialReference().IsSame(self._srs4326):
        #
        #     return self.GetEnvelope()[2]
        #
        # else:

        if self.GetSpatialReference().IsSame(self._srs4326):
            self.GetSpatialReference(). \
                SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        return self.GetEnvelope()[0]

    # -------------------------------------------------------------------------
    # uly
    # -------------------------------------------------------------------------
    def uly(self):

        # if self.GetSpatialReference().IsSame(self._srs4326):
        #
        #     return self.GetEnvelope()[1]
        #
        # else:

        if self.GetSpatialReference().IsSame(self._srs4326):
            self.GetSpatialReference(). \
                SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        return self.GetEnvelope()[3]

    # -------------------------------------------------------------------------
    # __setstate__
    #
    # e2 = pickle.loads(pickle.dumps(env))
    # -------------------------------------------------------------------------
    def __setstate__(self, state):

        multipointWkt = state[Envelope.MULTIPOINT_KEY]
        copy = ogr.CreateGeometryFromWkt(multipointWkt)
        self.__dict__.update(copy.__dict__)

        srsProj4 = state[Envelope.SRS_KEY]
        srs = SpatialReference()
        srs.ImportFromProj4(srsProj4)
        self.AssignSpatialReference(srs)

    # -------------------------------------------------------------------------
    # __getstate__
    # -------------------------------------------------------------------------
    # def __getstate__(self):
    #
    #     state = {Envelope.MULTIPOINT_KEY: self.ExportToWkt(),
    #             Envelope.SRS_KEY: self.GetSpatialReference().ExportToProj4()}
    #
    #     return state

    # -------------------------------------------------------------------------
    # __reduce__
    # -------------------------------------------------------------------------
    def __reduce__(self):

        state = {Envelope.MULTIPOINT_KEY: self.ExportToWkt(),
                 Envelope.SRS_KEY: self.GetSpatialReference().ExportToProj4()}

        return (self.__class__, (), state)
