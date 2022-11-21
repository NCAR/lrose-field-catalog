#!/usr/bin/env python

#======================================================================
#
# Create images for a DOW radar.  The DOW radar data is assumed to be
# in cfradial format.  The radar file must be read to get the location
# of the radar.
#
#======================================================================

from __future__ import print_function
import os
import sys
import time
import datetime
from datetime import timedelta
import string
import subprocess
from optparse import OptionParser
from stat import *
import math

def main():

    global options
    global fullFilePath
    global validTimeStr
    
    # parse the command line

    parseArgs()

    # initialize
    
    appName = __file__
    print("===========================================================")
    print("BEGIN: " + appName + " at " + str(datetime.datetime.now()))
    print("===========================================================")

    # Extract the radar latitutde/longitude from the volume
    
    radar_lat, radar_lon, fixed_angle = getRadarLatLon(fullFilePath);
    if (options.debug):
        print('==>> radar lat, lon, fixed_angle: ', radar_lat, ', ', radar_lon, ", ", fixed_angle)

    # Check the fixed anlgle.  We only process files between the sepcified fixed angles
    # to make sure we don't process the vertical scans

    #if (fixed_angle < options.min_fixed_angle) or (fixed_angle > options.max_fixed_angle):
    if (fixed_angle < options.min_fixed_angle) or (fixed_angle > options.max_fixed_angle) or ("RHI" in fullFilePath):
        print('**** Skipping scan with fixed angle outside of the specified range or RHI')
        return

    # Now get the radar x/y location assuming a Mercator projection with origin
    # latitude of 0.0 and longitude of the radar longitude

    radar_x, radar_y = getRadarXY(radar_lat, radar_lon)
    if (options.debug):
        print('radar_x = ', radar_x, ', radar_y = ', radar_y)

    # Set the environment variables that will be used in the CIDD
    # parameter file

    os.environ['DOW_RADAR_LAT'] = '%f' % radar_lat
    os.environ['DOW_RADAR_LON'] = '%f' % radar_lon
    
    os.environ['MERCATOR_MINY'] = '%f' % (radar_y - options.max_range_km)
    os.environ['MERCATOR_MAXY'] = '%f' % (radar_y + options.max_range_km)
    os.environ['MERCATOR_MINX'] = '%f' % (options.max_range_km * -1.0)
    os.environ['MERCATOR_MAXX'] = '%f' % (options.max_range_km)
    
    os.environ['FLAT_MINY'] = '%f' % (options.max_range_km * -1.0)
    os.environ['FLAT_MAXY'] = '%f' % (options.max_range_km)
    os.environ['FLAT_MINX'] = '%f' % (options.max_range_km * -1.0)
    os.environ['FLAT_MAXX'] = '%f' % (options.max_range_km)

    os.environ['MERCATOR_MINLAT'] = '%f' % (radar_lat - options.max_delta_lat)
    os.environ['MERCATOR_MAXLAT'] = '%f' % (radar_lat + options.max_delta_lat)
    os.environ['MERCATOR_MINLON'] = '%f' % (radar_lon - options.max_delta_lon)
    os.environ['MERCATOR_MAXLON'] = '%f' % (radar_lon + options.max_delta_lon)
    
    # create the images
    
    cmd = 'run_CIDD.catalog.' + options.radar_name + ' ' + validTimeStr
    print(cmd)
    runCommand(cmd);

    print("=============================================================")
    print("END: " + appName + " at " + str(datetime.datetime.now()))
    print("=============================================================")

    sys.exit(0)


########################################################################
# Parse the command line

def parseArgs():
    
    global options
    global fullFilePath
    global validTimeStr

    # parse the command line

    usage = "usage: %prog [options]"
    parser = OptionParser(usage)

    parser.add_option('--debug',
                      dest='debug', default=True,
                      action="store_true",
                      help='Set debugging on')

    parser.add_option('--verbose',
                      dest='verbose', default=False,
                      action="store_true",
                      help='Set verbose debugging on')

    parser.add_option('--abs_dir_path',
                      dest='abs_dir_path',
                      default='',
                      help='The full absolute path for the directory')

    parser.add_option('--rel_data_path',
                      dest='rel_data_path',
                      default='',
                      help='The file path relative to the absolute directory')

    parser.add_option('--valid_time',
                      dest='valid_time',
                      default='',
                      help='Comma-delimited valid time: yyyy,mm,dd,hh,mm,ss')

    # these options are specific to the radar

    parser.add_option('--radar_name',
                      dest='radar_name',
                      default='armor',
                      help='Type of image -- armor, chill, etc')

    # These options allow us to skip veritcal scans

    parser.add_option('--min_fixed_angle',
                      dest='min_fixed_angle',
                      type='float',
                      default='0.0',
                      help='Minimum fixed angle to process.')

    parser.add_option('--max_fixed_angle',
                      dest='max_fixed_angle',
                      type='float',
                      default='90.0',
                      help='Maximum fixed angle to process.')
    
    # max range

    parser.add_option('--max_range_km',
                      dest='max_range_km',
                      type='float',
                      default='130.0',
                      help='Max range for data.')

    parser.add_option('--max_delta_lat',
                      dest='max_delta_lat',
                      type='float',
                      default='1.25',
                      help='Delta latitude to max range - for Mercator images.')

    parser.add_option('--max_delta_lon',
                      dest='max_delta_lon',
                      type='float',
                      default='1.50',
                      help='Delta longitude to max range - for Mercator images.')

    (options, args) = parser.parse_args()
    
    # compute values derived from args

    fullFilePath = os.path.join(options.abs_dir_path, options.rel_data_path)

    (year, month, day, hour, min, sec) = options.valid_time.split(',')
    validTimeStr = year + month + day + hour + min + sec
    
    if (options.verbose):
        options.debug = True

    if (options.debug):
        print("Options:", file=sys.stderr)
        print("  debug? ", options.debug, file=sys.stderr)
        print("  verbose? ", options.verbose, file=sys.stderr)
        print("  abs_dir_path: ", options.abs_dir_path, file=sys.stderr)
        print("  rel_data_path: ", options.rel_data_path, file=sys.stderr)
        print("  fullFilePath: ", fullFilePath, file=sys.stderr)
        print("  valid_time: ", options.valid_time, file=sys.stderr)
        print("  validTimeStr: ", validTimeStr, file=sys.stderr)
        print("  radar_name: ", options.radar_name, file=sys.stderr)
        print("  min_fixed_angle: ", options.min_fixed_angle, file=sys.stderr)
        print("  max_fixed_angle: ", options.max_fixed_angle, file=sys.stderr)
        print("  max_range_km: ", options.max_range_km, file=sys.stderr)

########################################################################
# Extract the radar location from the given cfradial file

def getRadarLatLon(cfradial_file):

    # Use RadxPrint to write the volume to a temporary ASCII file

    tmp_file = '/tmp/cfradial.txt'

    cmd = 'RadxPrint -f ' + cfradial_file + ' >& ' + tmp_file
    runCommand(cmd)
    
    # Read in the ASCII file and pull out the radar location

    ascii_file = open(tmp_file, 'r')
    for line in ascii_file:
        if 'latitudeDeg:' in line:
            tokens = line.split()
            radar_lat = float(tokens[1])
        if 'longitudeDeg:' in line:
            tokens = line.split()
            radar_lon = float(tokens[1])
        if 'fixedAngle:' in line:
            tokens = line.split()
            fixed_angle = float(tokens[1])

    # Close the file and delete it

    ascii_file.close()
#    cmd = 'rm ' + tmp_file
#    runCommand(cmd)

    return radar_lat, radar_lon, fixed_angle

########################################################################
# Calculate the radar X/Y given the lat/lon.  We are using a Mercator projection with
# a latitude of 0.0 and longitude of the radar's longitude, so calculations are
# simplified

def getRadarXY(radar_lat, radar_lon):

    EradKm = 6378.137

    lat_rad = math.radians(radar_lat)
    lon_rad = math.radians(radar_lon)

    origin_lat_rad = 0.0
    origin_lon_rad = lon_rad

    dlon = 0.0

    x = 0.0
    y = EradKm * math.atanh(math.sin(lat_rad))

    return x, y

########################################################################
# Run a command in a shell, wait for it to complete

def runCommand(cmd):

    if (options.debug):
        print("running cmd:",cmd, file=sys.stderr)
    
    try:
        retcode = subprocess.call(cmd, shell=True)
        if retcode < 0:
            print("Child was terminated by signal: ", -retcode, file=sys.stderr)
        else:
            if (options.debug):
                print("Child returned code: ", retcode, file=sys.stderr)
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)

########################################################################
# kick off main method

if __name__ == "__main__":

   main()

