
from datetime import datetime
import logging
import os
# import psycopg2
import tempfile
from xml.dom import minidom

from osgeo.osr import CoordinateTransformation
from osgeo.osr import SpatialReference
from osgeo import osr

from core.model.Envelope import Envelope
from core.model.SystemCommand import SystemCommand


# -----------------------------------------------------------------------------
# class FootprintsQuery
# -----------------------------------------------------------------------------
class FootprintsQuery(object):

    BASE_QUERY = "ogr2ogr -f 'GML' --debug on"
    RUN_SENSORS = ['WV01', 'WV02', 'WV03']

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, logger=None):

        self.endDate = datetime.today()
        self.catalogIDs = []
        self.logger = logger
        self.maxScenes = -1
        self._minOverlapInDegrees = 0.0
        self.numBands = -1
        self.pairsOnly = False
        self.scenes = []
        self.sensors = []

        self.useMultispectral = True
        self.usePanchromatic = True
        self.useSwir = False

        self._envelope = None

    # -------------------------------------------------------------------------
    # addAoI
    # -------------------------------------------------------------------------
    def addAoI(self, envelope):

        # ---
        # Queries must be in geographic coordinates because this class uses
        # the ogr2ogr option -sql to sort the results.  When -sql is used
        # -spat_srs cannot be used.
        # ---
        targetSRS = SpatialReference()
        targetSRS.ImportFromEPSG(4326)

        if not envelope.GetSpatialReference().IsSame(targetSRS):
            envelope.TransformTo(targetSRS)

        self._envelope = envelope

    # -------------------------------------------------------------------------
    # addCatalogID
    # -------------------------------------------------------------------------
    def addCatalogID(self, catalogIDs=[]):

        self.catalogIDs.extend(catalogIDs)

    # -------------------------------------------------------------------------
    # addScenesFromNtf
    # -------------------------------------------------------------------------
    def addScenesFromNtf(self, ntfPaths=[]):

        # ---
        # It is acceptable to pass an NITF file that does not exist.  It could
        # have been erroneously deleted from the file system.
        # ---
        self.scenes.extend(ntfPaths)

    # -------------------------------------------------------------------------
    # addSensors
    # -------------------------------------------------------------------------
    def addSensors(self, sensors=[]):

        self.sensors.extend(sensors)

    # -------------------------------------------------------------------------
    # _buildWhereClausePostgres
    # -------------------------------------------------------------------------
    def _buildWhereClausePostgres(self):

        # Add level-1 data only, the start of a where clause.
        whereClause = "where (prod_code like '_1B_')"

        # Add sensor list.
        first = True
        sensors = self.sensors if self.sensors else FootprintsQuery.RUN_SENSORS

        for sensor in sensors:

            if first:

                first = False
                whereClause += ' AND ('

            else:
                whereClause += ' OR '

            whereClause += 'SENSOR=' + "'" + sensor + "'"

        if not first:
            whereClause += ')'

        # Add scene list.
        first = True

        for scene in self.scenes:

            if first:

                first = False

                whereClause += ' AND ('

            else:
                whereClause += ' OR '

            whereClause += 'S_FILEPATH=' + "'" + scene + "'"

        if not first:
            whereClause += ')'

        # Add pairs only clause.
        if self.pairsOnly:
            whereClause += ' AND (pairname IS NOT NULL)'

        # Add the catalog ID list.
        first = True

        for catID in self.catalogIDs:

            if first:

                first = False
                whereClause += ' AND ('

            else:
                whereClause += ' OR '

            whereClause += 'CATALOG_ID=' + "'" + catID + "'"

        if not first:
            whereClause += ')'

        # Set panchromatic or multispectral.
        if not self.usePanchromatic:
            whereClause += ' AND (SPEC_TYPE <> \'Panchromatic\' )'

        if not self.useMultispectral:
            whereClause += ' AND (SPEC_TYPE <> \'Multispectral\')'

        if not self.useSwir:
            whereClause += ' AND (SPEC_TYPE <> \'SWIR\')'

        # AoI
        if self._envelope:

            # ---
            # To filter scenes that only overlap the AoI slightly, decrease
            # both corners of the query AoI.
            # https://desktop.arcgis.com/en/arcmap/10.3/manage-data/using-sql-with-gdbs/st-intersects.htm
            # ---
            ulx = float(self._envelope.ulx()) + self._minOverlapInDegrees
            uly = float(self._envelope.uly()) - self._minOverlapInDegrees
            lrx = float(self._envelope.lrx()) - self._minOverlapInDegrees
            lry = float(self._envelope.lry()) + self._minOverlapInDegrees

            srs = self._envelope.GetSpatialReference()
            expandedEnv = Envelope()
            expandedEnv.addPoint(ulx, uly, 0, srs)
            expandedEnv.addPoint(lrx, lry, 0, srs)

            whereClause += ' AND (st_intersects(shape, ' + \
                           '\'' + expandedEnv.ExportToWkt() + '\'' + \
                           ') = \'t\')'

        return unicode(whereClause)

    # -------------------------------------------------------------------------
    # getScenes
    # -------------------------------------------------------------------------
    def getScenes(self):

        return self.getScenesFromGdb()

    # -------------------------------------------------------------------------
    # getScenesFromPostgres
    # -------------------------------------------------------------------------
    # def getScenesFromPostgres(self):
    #
    #     # Establish a DB connection.
    #     connection = psycopg2.connect(user='rlgill',
    #                                   password='HWrkaBlFcHhlE7NAq20S',
    #                                   host='arcdb02.atss.adapt.nccs.nasa.gov',
    #                                   database='arcgis_temp_test')
    #
    #     cursor = connection.cursor()
    #
    #     # Run the query.
    #     fields = ('sensor', 'acq_time', 'catalog_id', 'stereopair',
    #               's_filepath')
    #
    #     cmd = 'select ' + \
    #           ', '.join(fields) + \
    #           ' from footprint_nga_inventory_master ' + \
    #           self._buildWhereClausePostgres() + \
    #           ' order by acq_time desc'
    #
    #     if self.maxScenes > 0:
    #         cmd += ' limit ' + str(self.maxScenes)
    #
    #     if self.logger:
    #         self.logger.info(cmd)
    #
    #     cursor.execute(cmd)
    #
    #     # Store the results in FootprintScenes.
    #     dgFileNames = [record[4] for record in cursor]
    #
    #     # Close connections.
    #     if(connection):
    #
    #         cursor.close()
    #         connection.close()
    #
    #     return dgFileNames

    # -------------------------------------------------------------------------
    # setEndDate
    # -------------------------------------------------------------------------
    def setEndDate(self, endDateStr):

        endDate = datetime.strptime(endDateStr, '%Y-%m-%d')
        self.endDate = endDate

    # -------------------------------------------------------------------------
    # setMaximumScenes
    # -------------------------------------------------------------------------
    def setMaximumScenes(self, maximum):

        self.maxScenes = maximum

    # -------------------------------------------------------------------------
    # setMinimumOverlapInDegrees
    # -------------------------------------------------------------------------
    def setMinimumOverlapInDegrees(self, minimum=0.02):

        self._minOverlapInDegrees = minimum

    # -------------------------------------------------------------------------
    # setMultispectralOff
    # -------------------------------------------------------------------------
    def setMultispectralOff(self):

        self.useMultispectral = False

    # -------------------------------------------------------------------------
    # setNumBands
    # -------------------------------------------------------------------------
    def setNumBands(self, numBands):

        self.numBands = numBands

    # -------------------------------------------------------------------------
    # setPairsOnly
    # -------------------------------------------------------------------------
    def setPairsOnly(self, pairsOnly=True):

        self.pairsOnly = pairsOnly

    # -------------------------------------------------------------------------
    # setPanchromaticOff
    # -------------------------------------------------------------------------
    def setPanchromaticOff(self):

        self.usePanchromatic = False

    # -------------------------------------------------------------------------
    # setSwirOn
    # -------------------------------------------------------------------------
    def setSwirOn(self):

        self.useSwir = True

    # -------------------------------------------------------------------------
    # getScenesFromGdb
    # -------------------------------------------------------------------------
    def getScenesFromGdb(self):

        # Compose query.
        cmd = FootprintsQuery.BASE_QUERY

        if self.maxScenes > 0:
            cmd += ' -limit ' + str(self.maxScenes)

        if self._envelope:

            # ---
            # To filter scenes that only overlap the AoI slightly, decrease
            # both corners of the query AoI.
            # ---
            ulx = float(self._envelope.ulx()) + self._minOverlapInDegrees
            uly = float(self._envelope.uly()) - self._minOverlapInDegrees
            lrx = float(self._envelope.lrx()) - self._minOverlapInDegrees
            lry = float(self._envelope.lry()) + self._minOverlapInDegrees

            cmd += ' -spat' + \
                   ' ' + str(ulx) + \
                   ' ' + str(lry) + \
                   ' ' + str(lrx) + \
                   ' ' + str(uly)

        where = self._buildWhereClauseGdb()

        if len(where):

            # cmd += unicode(' -sql "select * from nga_inventory_canon ') + \
            #        where + \
            #        unicode(' order by ACQ_DATE DESC"')

            cmd += ' -sql "select * from nga_inventory_canon ' + \
                   where + \
                   ' order by ACQ_DATE DESC"'

        fpFile = '/css/nga/INDEX/Footprints/current/newest/' + \
                 'geodatabase/nga_inventory_canon.gdb'

        queryResult = tempfile.mkstemp()[1]
        cmd += ' "' + queryResult + '"  "' + fpFile + '" '
        SystemCommand(cmd, logger=self.logger, raiseException=True)

        resultGML = minidom.parse(queryResult)
        features = resultGML.getElementsByTagName('gml:featureMember')
        dgFileNames = []

        for feature in features:

            dgFileNames.append(feature.
                               getElementsByTagName('ogr:s_filepath')[0].
                               childNodes[0].
                               nodeValue)

        return dgFileNames

    # -------------------------------------------------------------------------
    # _buildWhereClauseGdb
    # -------------------------------------------------------------------------
    def _buildWhereClauseGdb(self):

        # Add level-1 data only, the start of a where clause.
        whereClause = "where (prod_short='1B')"

        # Add sensor list.
        first = True
        sensors = self.sensors if self.sensors else FootprintsQuery.RUN_SENSORS

        for sensor in sensors:

            if first:

                first = False
                whereClause += ' AND ('

            else:
                whereClause += ' OR '

            whereClause += 'SENSOR=' + "'" + sensor + "'"

        if not first:
            whereClause += ')'

        # Add pairs only clause.
        if self.pairsOnly:
            whereClause += ' AND (pairname IS NOT NULL)'

        # Add the catalog ID list.
        first = True

        for catID in self.catalogIDs:

            if first:

                first = False
                whereClause += ' AND ('

            else:
                whereClause += ' OR '

            whereClause += 'CATALOG_ID=' + "'" + catID + "'"

        if not first:
            whereClause += ')'

        # Set panchromatic or multispectral.
        if not self.usePanchromatic:
            whereClause += ' AND (SPEC_TYPE <> \'Panchromatic\' )'

        if not self.useMultispectral:
            whereClause += ' AND (SPEC_TYPE <> \'Multispectral\')'

        # Set bands.
        if self.numBands > 0:
            whereClause += ' AND (BANDS=\'' + str(self.numBands) + '\')'

        # Set end date.  "2018/07/02 00:00:00"
        whereClause += ' AND (ACQ_DATE<\'' + \
                       self.endDate.strftime("%Y-%m-%d %H:%M:%S") + \
                       '\')'

        # return unicode(whereClause)
        return whereClause
