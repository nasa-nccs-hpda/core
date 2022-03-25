# -*- coding: utf-8 -*-

import os
import shutil
import warnings

from osgeo import osr
from osgeo.osr import SpatialReference

import pandas
from pandas.tseries.offsets import MonthEnd

from core.model.GeospatialImageFile import GeospatialImageFile


# -----------------------------------------------------------------------------
# class MerraRequest
#
# MERRA description:  https://gmao.gsfc.nasa.gov/pubs/docs/Bosilovich785.pdf
# -----------------------------------------------------------------------------
class MerraRequest(object):

    BASE_DIR = '/adapt/nobackup/projects/ilab/data/MERRA2/'
    OPERATIONS = ['avg', 'max', 'min', 'sum']
    MONTHLY = 'monthly'
    WEEKLY = 'weekly'
    FREQUENCY = [MONTHLY, WEEKLY]

    # -------------------------------------------------------------------------
    # _adjustFrequency
    # -------------------------------------------------------------------------
    @staticmethod
    def _adjustFrequency(dateRange, frequency):

        if frequency not in MerraRequest.FREQUENCY:

            raise RuntimeError('Frequency, ' +
                               str(frequency) +
                               ', is invalid.')
        # ---
        # Reduce the input date range frequency from days to the specified
        # frequency.
        # ['2000-08-02', '2000-08-03', ...] becomes
        # ['2000-08-31', '2000-09-30', ...]
        #
        # When converting to months, Pandas will exclude the final month
        # unless the date is the last day of the month.  Round the end date
        # to be the last day of the month.
        # ---
        endDate = dateRange[-1] + MonthEnd(0)

        pandasFreq = {MerraRequest.MONTHLY: 'M', MerraRequest.WEEKLY: 'W'}

        adjustedRange = pandas.date_range(dateRange[0],
                                          endDate,
                                          None,
                                          pandasFreq[frequency])

        # ---
        # The query in which these dates are involved expresses dates as
        # yyyy_freq## (2008_week05, 1994_month03).  Reformat the date_range
        # to match the query format.
        # ---
        reformattedRange = []
        fileFreq = {MerraRequest.MONTHLY: 'month', MerraRequest.WEEKLY: 'week'}

        for d in adjustedRange:

            freq = d.week if frequency == MerraRequest.WEEKLY else d.month

            reformattedRange.append(str(d.year) +
                                    '_' +
                                    fileFreq[frequency] +
                                    str(freq).zfill(2))

        return reformattedRange

    # -------------------------------------------------------------------------
    # extractVars
    # -------------------------------------------------------------------------
    @staticmethod
    def _extractVars(files, variables, envelope, outDir):

        srs = SpatialReference()
        srs.ImportFromEPSG(4326)
        srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        subFiles = []

        for f in files:

            geoFile = GeospatialImageFile(f, srs)
            subs = geoFile._getDataset().GetSubDatasets()
            foundVariables = []

            # Look for a variable name in the subdataset name.
            for sub in subs:

                datasetName = sub[0]
                var = datasetName.split(':')[2]

                if var in variables:

                    foundVariables.append(var)

                    # ---
                    # Copy the original file before operating on it, unless
                    # it already exists in the output directory.
                    # ---
                    name = os.path.basename(os.path.splitext(f)[0]) + \
                        '_' + \
                        var + \
                        '.nc'

                    workingCopy = os.path.join(outDir, name)

                    if not os.path.exists(workingCopy):

                        shutil.copyfile(f, workingCopy)

                        # Extract and clip the subdataset.
                        copyGeoFile = GeospatialImageFile(workingCopy, srs)
                        copyGeoFile.clipReproject(envelope, None, sub[0])

                    else:
                        copyGeoFile = GeospatialImageFile(workingCopy, srs)

                    subFiles.append(copyGeoFile.fileName())

                    # Stop, when all variables are found.
                    if len(foundVariables) == len(variables):
                        break

            # Are any variables missing?
            if len(foundVariables) != len(variables):

                missing = [v for v in variables if v not in foundVariables]
                msg = 'Variables not found in ' + str(f) + ': ' + str(missing)
                raise RuntimeError(msg)

        return subFiles

    # -------------------------------------------------------------------------
    # query
    # -------------------------------------------------------------------------
    @staticmethod
    def queryFiles(dateRange, frequency, collections, operations):

        # ---
        # Images of different frequencies are stored in separate
        # subdirectories.  Set the correct subdirectory.
        # ---
        subdirs = {MerraRequest.MONTHLY: 'Monthly',
                   MerraRequest.WEEKLY: 'Weekly'}

        queryPath = os.path.join(MerraRequest.BASE_DIR + subdirs[frequency])

        # ---
        # There is a file for each frequency step in the date range, like
        # ...month02..., ...month03..., ...month04.... A date range object
        # has a default frequency of daily and is in a different format than
        # that of our MERRA file names.  Express the date range in the format
        # and frequency of our MERRA file names.
        # ---
        adjDateRange = MerraRequest._adjustFrequency(dateRange, frequency)

        # ---
        # Find the files.  We could use glob and build a regular expression to
        # return all the dates, variables and operations in one glob.  Instead,
        # find each file individually.  We must detect any missing files.
        # Finding files individually helps with this, and it is easier to read.
        # Using one glob, we would still need to loop through the results to
        # detect missing files.
        # ---
        existingFiles = []
        missingFiles = []

        for coll in collections:

            for op in operations:

                if op not in MerraRequest.OPERATIONS:
                    raise RuntimeError('Invalid operation: ' + str(op))

                for date in adjDateRange:

                    fileName = os.path.join(queryPath,
                                            coll +
                                            '_' +
                                            op +
                                            '_' +
                                            date +
                                            '.nc')

                    if os.path.exists(fileName):

                        existingFiles.append(fileName)

                    else:
                        missingFiles.append(fileName)

        return existingFiles, missingFiles

    # -------------------------------------------------------------------------
    # run
    # -------------------------------------------------------------------------
    @staticmethod
    def run(envelope, dateRange, frequency, collections, variables, operations,
            outDir):

        # Validate the input.
        MerraRequest._validateInput(outDir)

        # Get the raw files.
        results, missingFiles = \
            MerraRequest.queryFiles(dateRange, frequency, collections,
                                    operations)

        if not results:
            raise RuntimeError('No MERRA files satisfy the request.')

        if missingFiles:

            warnings.warn('The request parameters encompass the following ' +
                          'files; however, they do not exist.\n' +
                          str(missingFiles))

        # Extract the variables.
        clippedFiles = MerraRequest._extractVars(results, variables, envelope,
                                                 outDir)

        return clippedFiles

    # -------------------------------------------------------------------------
    # _validateInput
    # -------------------------------------------------------------------------
    @staticmethod
    def _validateInput(outDir):

        # Validate outdir.
        if not os.path.exists(outDir):

            raise RuntimeError('Output directory' +
                               str(outDir) +
                               ' does not exist.')

        if not os.path.isdir(outDir):

            raise RuntimeError('Output directory' +
                               str(outDir) +
                               ' must be a directory.')
