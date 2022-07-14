
from datetime import datetime
import logging
import psycopg2
import tempfile
from xml.dom import minidom

from osgeo.osr import SpatialReference
from osgeo import osr

from core.model.Envelope import Envelope
from core.model.FootprintsScene import FootprintsScene
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
        self.pairNames = []
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
        targetSRS.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        if not envelope.GetSpatialReference().IsSame(targetSRS):
            envelope.TransformTo(targetSRS)

        self._envelope = envelope

    # -------------------------------------------------------------------------
    # addCatalogID
    # -------------------------------------------------------------------------
    def addCatalogID(self, catalogIDs=[]):

        self.catalogIDs.extend(catalogIDs)

    # -------------------------------------------------------------------------
    # addPairName
    # -------------------------------------------------------------------------
    def addPairNames(self, pairNames):

        self.pairNames.extend(pairNames)

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

        # Include only valid records.
        whereClause += " AND (status like 'validated%' or " + \
                       "status = 'previewjpg_path_fail')"

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

        # ---
        # Add pair name list.
        # ---
        first = True

        for pairName in self.pairNames:

            if first:

                first = False
                whereClause += ' AND ('

            else:
                whereClause += ' OR '

            whereClause += 'pairname=' + "'" + pairName + "'"

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

        # Set bands.
        if self.numBands > 0:
            whereClause += ' AND (BANDS=\'' + str(self.numBands) + '\')'

        # Set end date.  "2018/07/02 00:00:00"
        whereClause += ' AND (ACQ_DATE<\'' + \
                       self.endDate.strftime("%Y-%m-%d %H:%M:%S") + \
                       '\')'

        # return unicode(whereClause)
        return whereClause

    # -------------------------------------------------------------------------
    # getScenes
    # -------------------------------------------------------------------------
    def getScenes(self):

        # return self.getScenesFromGdb()
        return self.getScenesFromPostgres()

    # -------------------------------------------------------------------------
    # getScenesFromResultsFile
    # -------------------------------------------------------------------------
    def getScenesFromResultsFile(self, resultsFile):

        resultGML = minidom.parse(resultsFile)
        features = resultGML.getElementsByTagName('gml:featureMember')
        fpScenes = [FootprintsScene(f) for f in features]

        return fpScenes

    # -------------------------------------------------------------------------
    # getScenesFromPostgres
    # -------------------------------------------------------------------------
    def getScenesFromPostgres(self):

        # ---
        # Establish a DB connection.
        # https://www.postgresql.org/docs/current/libpq-pgpass.html
        # ---
        connection = psycopg2.connect(user='nga_user',
                                      password='8iO00c43TMusKRZoJqXt',
                                      host='arcdb04.atss.adapt.nccs.nasa.gov',
                                      port='5432',
                                      database='arcgis')

        cursor = connection.cursor()

        # Run the query.
        fields = ('s_filepath', 'stereopair', 'strip_id')

        cmd = 'select ' + \
              ', '.join(fields) + \
              ' from nga_footprint_master_v2 ' + \
              self._buildWhereClausePostgres() + \
              ' order by acq_time desc'

        if self.maxScenes > 0:
            cmd += ' limit ' + str(self.maxScenes)

        if self.logger:
            self.logger.info(cmd)

        # psycopg2.extensions.cursor
        cursor.execute(cmd)

        # Store the results in FootprintScenes.
        fpScenes = [FootprintsScene(record) for record in cursor]

        # Close connections.
        if(connection):

            cursor.close()
            connection.close()

        return fpScenes

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

            cmd += ' -sql "select * from nga_footprint_master_v2 ' + \
                   where + \
                   ' order by ACQ_DATE DESC"'

        fpFile = '/css/nga/INDEX/current/nga_footprint.gdb'

        queryResult = tempfile.mkstemp()[1]
        cmd += ' "' + queryResult + '"  "' + fpFile + '" '
        SystemCommand(cmd, logger=self.logger, raiseException=True)

        fpScenes = self.getScenesFromResultsFile(queryResult)

        return fpScenes

    # -------------------------------------------------------------------------
    # fpScenesToFileNames
    # -------------------------------------------------------------------------
    def fpScenesToFileNames(self, fpScenes):

        return [f.fileName() for f in fpScenes]

    # -------------------------------------------------------------------------
    # _buildWhereClauseGdb
    # -------------------------------------------------------------------------
    def _buildWhereClauseGdb(self):

        # Add level-1 data only, the start of a where clause.
        whereClause = "where (prod_short='1B')"

        # Include only valid records.
        whereClause += " AND (status like 'validated%' or " + \
                       "status = 'previewjpg_path_fail')"

        # ---
        # Add sensor list.
        # ---
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

        # ---
        # Add pair name list.
        # ---
        first = True

        for pairName in self.pairNames:

            if first:

                first = False
                whereClause += ' AND ('

            else:
                whereClause += ' OR '

            whereClause += 'pairname=' + "'" + pairName + "'"

        if not first:
            whereClause += ')'

        # ---
        # Add scene list.
        # ---
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

        # ---
        # Add the catalog ID list.
        # ---
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
