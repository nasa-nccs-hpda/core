
from datetime import datetime
import os
import shutil
import xml.etree.ElementTree as ET

from osgeo.osr import SpatialReference
from osgeo import gdal
from osgeo import osr

from core.model.Envelope import Envelope
from core.model.GeospatialImageFile import GeospatialImageFile
from core.model.SystemCommand import SystemCommand


# -----------------------------------------------------------------------------
# class DgFile
#
# This class represents a Digital Globe file.  It is a single NITF file or a
# GeoTiff with an XML counterpart.  It is unique because of the metadata tags
# within.
# -----------------------------------------------------------------------------
class DgFile(GeospatialImageFile):

    # -------------------------------------------------------------------------
    # __init__
    # -------------------------------------------------------------------------
    def __init__(self, fileName, logger=None):

        # Check that the file is NITF or TIFF
        extension = os.path.splitext(fileName)[1]

        if extension != '.ntf' and extension != '.tif':
            raise RuntimeError('{} is not a NITF or TIFF'.format(fileName))

        self.extension = extension

        # Ensure the XML file exists.
        xmlFileName = fileName.replace(self.extension, '.xml')

        if not os.path.exists(xmlFileName):
            raise FileNotFoundError('{} does not exist'.format(xmlFileName))

        self.xmlFileName = xmlFileName

        # ---
        # Initialize the base class.  Wrap in a try-catch block because there
        # is a good chance that the SRS will be invalid.  This is handled
        # below.
        # ---
        try:
            super(DgFile, self).__init__(fileName,
                                         spatialReference=None,
                                         logger=logger)

        except RuntimeError as e:

            # ---
            # It could also be the case that the file is corrupt.  This means
            # GDAL will fail when it tries to open the dataset.
            # ---
            if not self._dataset:
                raise e

        # Some data members require the XML file counterpart to the TIF.
        tree = ET.parse(self.xmlFileName)
        self.imdTag = tree.getroot().find('IMD')

        if self.imdTag is None:

            raise RuntimeError('Unable to locate the "IMD" tag in ' +
                               self.xmlFileName)

        # ---
        # DG files do not always have spatial information in the file.  In
        # these cases, this information must be extracted from the file's
        # XML counterpart.  Unlike with normal GeospatialImageFiles we must
        # store the corner points for this case.  GeospatialImageFile.envelope
        # is overridden below to use these points, when they exist.
        # ---
        self._ulx = None
        self._uly = None
        self._lrx = None
        self._lry = None

        # If srs from GdalFile is empty, set srs, and get coords from the .xml.
        # if not self._dataset.GetSpatialRef():

        # ---
        # Below is a temporary fix until ASP fixes dg_mosaic bug.
        # Dg_mosaic outputs, along with a strip .tif, an aggregate .xml
        # file for all scene inputs. The tif has no projection information,
        # so we have to get that from the output .xml. All bands *should*
        # have same extent in the .xml but a bug with ASP does not ensure
        # this is always true.
        #
        # For 4-band mosaics, output extent is consitent among all bands.
        # For 8-band mosaics, the first band (BAND_C) is not updated in the
        # output .xml, so we have to use second band (BAND_B).
        #
        # if no bug, first BAND tag will work for 8-band, 4-band, 1-band.
        # ---
        try:
            bandTag = [n for n in self.imdTag if
                       n.tag.startswith('BAND_B')][0]

        except IndexError:  # Pan only has BAND_P

            try:
                bandTag = [n for n in self.imdTag if
                           n.tag.startswith('BAND_P')][0]

            except IndexError:

                bandTag = [n for n in self.imdTag if
                           n.tag.startswith('BAND_S')][0]

        self._ulx = min(float(bandTag.find('LLLON').text),
                        float(bandTag.find('ULLON').text))

        self._uly = max(float(bandTag.find('ULLAT').text),
                        float(bandTag.find('URLAT').text))

        self._lrx = max(float(bandTag.find('LRLON').text),
                        float(bandTag.find('URLON').text))

        self._lry = min(float(bandTag.find('LRLAT').text),
                        float(bandTag.find('LLLAT').text))

        self.validateCoordinates()  # Lastly, validate coordinates

        # bandNameList
        try:
            self.bandNameList = \
                [n.tag for n in self.imdTag if n.tag.startswith('BAND_')]

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            self.bandNameList = None

        # numBands
        try:
            self.numBands = self._dataset.RasterCount

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            self.numBands = None

        self.footprintsGml = None

    # -------------------------------------------------------------------------
    # abscalFactor()
    # -------------------------------------------------------------------------
    def abscalFactor(self, bandName):

        if isinstance(bandName, str) and bandName.startswith('BAND_'):

            return float(self.imdTag.find(bandName).find('ABSCALFACTOR').text)

        else:
            raise RuntimeError('Could not retrieve abscal factor.')

    # -------------------------------------------------------------------------
    # cloudCover()
    # -------------------------------------------------------------------------
    def cloudCover(self):

        try:
            cc = self.imdTag.find('IMAGE').find('CLOUDCOVER').text

            if cc is None:
                cc = self._dataset.GetMetadataItem('NITF_PIAIMC_CLOUDCVR')

            return float(cc)

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            return None

    # -------------------------------------------------------------------------
    # effectiveBandwidth()
    # -------------------------------------------------------------------------
    def effectiveBandwidth(self, bandName):

        if isinstance(bandName, str) and bandName.startswith('BAND_'):

            return float(self.imdTag.
                         find(bandName).
                         find('EFFECTIVEBANDWIDTH').text)

        else:
            raise RuntimeError('Could not retrieve effective bandwidth.')

    # -------------------------------------------------------------------------
    # envelope
    # -------------------------------------------------------------------------
    def envelope(self):

        envelope = Envelope()
        envelope.addPoint(self._ulx, self._uly, 0, self.srs())
        envelope.addPoint(self._lrx, self._lry, 0, self.srs())

        return envelope

    # -------------------------------------------------------------------------
    # firstLineTime()
    # -------------------------------------------------------------------------
    def firstLineTime(self):

        try:
            t = self._dataset.GetMetadataItem('NITF_CSDIDA_TIME')

            if t is not None:
                return datetime.strptime(t, "%Y%m%d%H%M%S")

            else:
                t = self.imdTag.find('IMAGE').find('FIRSTLINETIME').text
                return datetime.strptime(t, "%Y-%m-%dT%H:%M:%S.%fZ")

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            return None

    # -------------------------------------------------------------------------
    # getBand()
    # -------------------------------------------------------------------------
    def getBand(self, outputDir, bandName):

        gdalBandIndex = int(self.bandNameList.index(bandName)) + 1

        baseName = \
            os.path.basename(self.fileName().
                             replace(self.extension,
                                     '_b{}.tif'.format(gdalBandIndex)))

        tempBandFile = os.path.join(outputDir, baseName)

        if not os.path.exists(tempBandFile):

            cmd = 'gdal_translate' + \
                  ' -b {}'.format(gdalBandIndex) + \
                  ' -a_nodata 0' + \
                  ' -strict' + \
                  ' -mo "bandName={}"'.format(bandName) + \
                  ' ' + self.fileName() + \
                  ' ' + tempBandFile

            sCmd = SystemCommand(cmd, self.logger)

            if sCmd.returnCode:
                tempBandFile = None

        # Copy scene .xml to accompany the extracted .tif for dg_mosaic
        shutil.copy(self.xmlFileName, tempBandFile.replace('.tif', '.xml'))

        return tempBandFile

    # -------------------------------------------------------------------------
    # getBandName()
    # -------------------------------------------------------------------------
    def getBandName(self):

        try:
            return self._dataset.GetMetadataItem('bandName')

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            return None

    # -------------------------------------------------------------------------
    # getCatalogId()
    # -------------------------------------------------------------------------
    def getCatalogId(self):

        return self.imdTag.findall('./IMAGE/CATID')[0].text

    # -------------------------------------------------------------------------
    # getField
    # -------------------------------------------------------------------------
    def getField(self, nitfTag, xmlTag):

        try:

            value = self._dataset.GetMetadataItem(nitfTag)

            if not value:
                value = self.imdTag.find('IMAGE').find(xmlTag).text

            return float(value)

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            return None

    # -------------------------------------------------------------------------
    # getStripName()
    # -------------------------------------------------------------------------
    def getStripName(self):

        try:
            prodCode = None

            if self.specTypeCode() == 'MS':

                prodCode = 'M1BS'

            else:
                prodCode = 'P1BS'

            dateStr = '{}{}{}'.format(self.year(),
                                      str(self.firstLineTime().month).zfill(2),
                                      str(self.firstLineTime().day).zfill(2))

            return '{}_{}_{}_{}'.format(self.sensor(),
                                        dateStr,
                                        prodCode,
                                        self.getCatalogId())

        except Exception as e:

            if self.logger:
                self.logger.warn(e)

            return None

    # -------------------------------------------------------------------------
    # getStripIndex
    # -------------------------------------------------------------------------
    def getStripIndex(self):

        return os.path.splitext(self.fileName())[0].split('_')[-1]

    # -------------------------------------------------------------------------
    # isMate
    #
    # A pair name is *only available from Footprints*, and it looks like
    # WV02_20181005_10300100889D0300_10300100869C3C00, where the pair consists
    # of mates identified by the catalog IDs 10300100889D0300 and
    # 10300100869C3C00.  Furthermore, these catalog IDs represent strips, so
    # there can be multiple scenes for each ID.  To determine the mate, *match
    # the last part of the file name* from the file naming convention.  This is
    # what happens when non-computer scientists design systems.
    # -------------------------------------------------------------------------
    def isMate(self, pairName, otherDgf):

        pairCats = pairName.split('_')[2:]
        thisCat = self.getCatalogId()

        if thisCat not in pairCats:

            raise ValueError('Pair name, ' +
                             str(pairName) +
                             ' is unassociated with this file.')

        otherCat = otherDgf.getCatalogId()

        if otherCat not in pairCats:
            return False

        if otherCat == thisCat:
            return False

        if self.getStripIndex() != otherDgf.getStripIndex():
            return False

        return True

    # -------------------------------------------------------------------------
    # isMultispectral()
    # -------------------------------------------------------------------------
    def isMultispectral(self):

        return self.specTypeCode() == 'MS'

    # -------------------------------------------------------------------------
    # isPanchromatic()
    # -------------------------------------------------------------------------
    def isPanchromatic(self):

        return self.specTypeCode() == 'PAN'

    # -------------------------------------------------------------------------
    # isSwir
    # -------------------------------------------------------------------------
    def isSwir(self):

        return self.specTypeCode() == 'SWIR'

    # -------------------------------------------------------------------------
    # meanSatelliteAzimuth
    # -------------------------------------------------------------------------
    def meanSatelliteAzimuth(self):

        return self.getField('NITF_CSEXRA_AZ_OF_OBLIQUITY', 'MEANSATAZ')

    # -------------------------------------------------------------------------
    # meanSatelliteElevation
    # -------------------------------------------------------------------------
    def meanSatelliteElevation(self):

        return self.getField('', 'MEANSATEL')

    # -------------------------------------------------------------------------
    # meanSunAzimuth
    # -------------------------------------------------------------------------
    def meanSunAzimuth(self):

        return self.getField('NITF_CSEXRA_SUN_AZIMUTH', 'MEANSUNAZ')

    # -------------------------------------------------------------------------
    # meanSunElevation()
    # -------------------------------------------------------------------------
    def meanSunElevation(self):

        return self.getField('NITF_CSEXRA_SUN_ELEVATION', 'MEANSUNEL')

    # -------------------------------------------------------------------------
    # prodLevelCode()
    # -------------------------------------------------------------------------
    def prodLevelCode(self):

        try:
            return self.imdTag.find('PRODUCTLEVEL').text

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            return None

    # -------------------------------------------------------------------------
    # sensor()
    # -------------------------------------------------------------------------
    def sensor(self):

        try:
            sens = self._dataset.GetMetadataItem('NITF_PIAIMC_SENSNAME')

            if not sens:
                sens = self.imdTag.find('IMAGE').find('SATID').text

            return sens

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            pass

        return None

    # -------------------------------------------------------------------------
    # setBandName()
    # -------------------------------------------------------------------------
    def setBandName(self, bandName):

        self._dataset.SetMetadataItem("bandName", bandName)

    # -------------------------------------------------------------------------
    # specTypeCode()
    # -------------------------------------------------------------------------
    def specTypeCode(self):

        try:
            stc = self._dataset.GetMetadataItem('NITF_CSEXRA_SENSOR')

            if stc is None:

                if self.imdTag.find('BANDID').text == 'P':
                    stc = 'PAN'

                elif self.imdTag.find('BANDID').text == 'MS1' or \
                        self.imdTag.find('BANDID').text == 'Multi':

                    stc = 'MS'

            return stc

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            return None

    # -------------------------------------------------------------------------
    # srs
    # -------------------------------------------------------------------------
    def srs(self):

        srs = self._dataset.GetSpatialRef()

        if not srs:
            srs = SpatialReference()
            srs.ImportFromEPSG(4326)
            srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        return srs

    # -------------------------------------------------------------------------
    # toBandInterleavedBinary()
    # -------------------------------------------------------------------------
    def toBandInterleavedBinary(self, outputDir):

        outBin = \
            os.path.join(outputDir,
                         os.path.basename(self.fileName.replace(self.extension,
                                                                '.bin')))

        try:
            ds = gdal.Open(self.fileName)

            ds = gdal.Translate(outBin,
                                ds,
                                creationOptions=["INTERLEAVE=BAND"])

            ds = None
            return outBin

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            return None

    # -------------------------------------------------------------------------
    # validateCoordinates()
    #
    # Sometimes the input file will have ulx and lrx and/or uly and lry
    # swapped.  Detect and fix this.
    # -------------------------------------------------------------------------
    def validateCoordinates(self):

        if self._ulx > self._lrx:

            temp = self._ulx
            self._ulx = self._lrx
            self._lrx = temp

        if self._lry > self._uly:

            temp = self._lry
            self._lry = self._uly
            self._uly = temp

    # -------------------------------------------------------------------------
    # year()
    # -------------------------------------------------------------------------
    def year(self):

        try:
            yr = self._dataset.GetMetadataItem('NITF_CSDIDA_YEAR')

            if yr is None:
                yr = self.firstLineTime().year

            return yr

        except Exception as e:

            if self._logger:
                self._logger.info(e)

            return None

    # -------------------------------------------------------------------------
    # __setstate__
    #
    # e2 = pickle.loads(pickle.dumps(env))
    # -------------------------------------------------------------------------
    def __setstate__(self, state):

        self.__init__(state[GeospatialImageFile.FILE_KEY],
                      state[GeospatialImageFile.LOGGER_KEY])
