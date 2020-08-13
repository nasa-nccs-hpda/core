#!/usr/bin/python
import argparse
import sys
import pandas

from osgeo.osr import SpatialReference

from core.model.Envelope import Envelope
from core.model.MerraRequest import MerraRequest


# -----------------------------------------------------------------------------
# main
#
# cd innovation-lab
# export PYTHONPATH=`pwd`
# view/MerraRequestCLV.py -e -125 50 -66 24 --epsg 4326 --start_date 2013-02-03 --end_date 2013-03-12 -c m2t1nxslv --vars QV2M TS --op avg -o /att/nobackup/rlgill/testMerraReq/
# -----------------------------------------------------------------------------
def main():

    # Process command-line args.
    desc = 'Use this application to request MERRA files.'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-e',
                        required=True,
                        nargs='+',
                        help='ulx uly lrx lry')

    parser.add_argument('--epsg',
                        required=True,
                        type=int,
                        help='EPSG code')

    parser.add_argument('--start_date',
                        required=True,
                        help='YYYY-MM-DD')

    parser.add_argument('--end_date',
                        required=True,
                        help='YYYY-MM-DD')

    parser.add_argument('-c',
                        required=True,
                        help='Name of collection of MERRA2')

    parser.add_argument('--vars',
                        required=True,
                        nargs='+',
                        help='List of variables in M2 collection')

    parser.add_argument('--op',
                        required=True,
                        help='Type of analysis')

    parser.add_argument('-o',
                        default='.',
                        help='Path to output directory')

    args = parser.parse_args()

    # Envelope
    srs = SpatialReference()
    srs.ImportFromEPSG(args.epsg)
    env = Envelope()
    env.addPoint(float(args.e[0]), float(args.e[1]), 0, srs)
    env.addPoint(float(args.e[2]), float(args.e[3]), 0, srs)

    # Date Range
    dateRange = pandas.date_range(args.start_date, args.end_date)

    # Mas Request
    MerraRequest.run(env, dateRange, MerraRequest.MONTHLY, [args.c],
                     args.vars, [args.op], args.o)

# -----------------------------------------------------------------------------
# Invoke the main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(main())
