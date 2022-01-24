#!/usr/bin/env python

#===========================================================================
#
# Put DOW images data to catalog.
#
#===========================================================================

from __future__ import print_function
import os
import sys
from stat import *
import time
import datetime
from datetime import timedelta
import string
import ftplib
import subprocess
from optparse import OptionParser
import xml.etree.ElementTree as ET

def main():

    appName = __file__

    global options

    # parse the command line

    parseArgs()

    # initialize
    
    if (options.debug):
        print("=======================================================", file=sys.stderr)
        print("BEGIN: " + appName + " " + str(datetime.datetime.now()), file=sys.stderr)
        print("=======================================================", file=sys.stderr)

    # create tmp dir if necessary
    
    if not os.path.exists(options.tempDir):
        runCommand("mkdir -p " + options.tempDir)

    #   compute valid time string

    unixTime = time.gmtime(int(options.unixTime))
    year = int(unixTime[0])
    month = int(unixTime[1])
    day = int(unixTime[2])
    hour = int(unixTime[3])
    minute = int(unixTime[4])
    sec = int(unixTime[5])
    yyyymmdd = "%.4d%.2d%.2d" % (year, month, day)
    hh = "%.2d" % hour
    mm = "%.2d" % minute
    validDayStr = "%.4d%.2d%.2d" % (year, month, day)
    validTimeStr = "%.4d%.2d%.2d%.2d%.2d" % (year, month, day, hour, minute)
    dateTimeStr = "%.4d%.2d%.2d-%.2d%.2d%.2d" % (year, month, day, hour, minute, sec)

    # compute full path of image
    
    dataDir = os.environ['DATA_DIR']
    incomingFilePath = os.path.join(dataDir, options.relFilePath);
    
    # extract the platform and product from the file name.
    # The image files are named like:
    #   <category>.<legend_label>.<button_label>.<platform>.<time>.png.
    # For example:
    #   radar.DOW6-DBZ.DBZ.DOW6.20150520232246.png (normal)
    #   radar.DOW6-DBZ.DBZ-TRANS.DOW6.20150520232246.png (transparent)

    file_tokens = options.fileName.split(".")
    if (options.debug):
        print("filename toks: ", file=sys.stderr)
        print(file_tokens, file=sys.stderr)
        
    if len(file_tokens) != 6:
        print("*** Invalid file name: ", options.fileName)
        sys.exit(0)

    # check for valid time

    timeStr = file_tokens[4]
    yearStr = timeStr[0:4]
    year = int(yearStr)
    if (year < 2018):
        print("!!! ==>> Invalid time string: ", yearStr, file=sys.stderr)
        sys.exit(0)
    dayStr = timeStr[0:8]

    # incoming category

    inCat = file_tokens[0]
    if (inCat != 'radar'):
        print("!!! ==>> Bad incoming category: ", inCat, file=sys.stderr)
        print("         Should be 'radar'", file=sys.stderr)
        sys.exit(0)

    # field
        
    catalogFieldName = file_tokens[2]

    # platform name

    platform = file_tokens[3]

    # extension

    extension = file_tokens[5]

    catalogFileName = ("radar." + platform + "." +
                       validTimeStr + "." +
                       catalogFieldName + "." +
                       extension)

    if (options.debug):
        print("catalogFileName: ", catalogFileName, file=sys.stderr)

    # put the image file
    
    ftpFile(incomingFilePath, catalogFileName)

    # create and put the associated KML file, only for transparent images

    if (catalogFieldName.find("-TRANS") >= 0):

        # gis.DOW#.YYYYMMDDHHmm.catalogFieldName.kml

        xmlFilePath = incomingFilePath[:-3] + "xml"

        kmlCatalogName = "gis." + platform + "." + \
                         yyyymmdd + hh + mm + "." + \
                         catalogFieldName + ".kml"
        
        kmlFilePath = os.path.join(options.tempDir, kmlCatalogName)
        
        if (options.debug):
            print("creating kml file: ", kmlFilePath, file=sys.stderr)
            
        createKmlFile(xmlFilePath, kmlFilePath,
                      options.catalogCategory, platform, yyyymmdd, hh, mm, catalogFieldName)
        ftpFile(kmlFilePath, kmlCatalogName)

        # Delete the temporary KML file
        
        #cmd = 'rm ' + kmlFilePath
        #runCommand(cmd)

    # let the user know we are done

    if (options.debug):
        print("=======================================================", file=sys.stderr)
        print("END: " + appName + " " + str(datetime.datetime.now()), file=sys.stderr)
        print("=======================================================", file=sys.stderr)

    sys.exit(0)

########################################################################
# Create the KML file using the information from the XML file generated
# by CIDD.

def createKmlFile(xmlPath, kmlPath, category, platform,
                  yyyymmdd, hh, mm, catalogFieldName):

    # Pull the lat/lon limits of the image from the XML file.

    tree = ET.parse(xmlPath)
    lat_lon_box = tree.getroot().find('LatLonBox')
    north = lat_lon_box.find('north').text
    south = lat_lon_box.find('south').text
    west = lat_lon_box.find('west').text
    east = lat_lon_box.find('east').text

    if (options.debug):
        print('north = ', north)
        print('south = ', south)
        print('east = ', east)
        print('west = ', west)
    
    # Construct the HREF for this file
    # this is the platform in lower case

    href_platform = platform.lower()
    catalog_name = options.catalogName
    
    href = 'http://catalog.eol.ucar.edu/' + catalog_name + '/radar/' \
           + href_platform + '/' + yyyymmdd + '/' + hh \
           + '/radar.' + platform + '.' + yyyymmdd + hh + mm + '.' + catalogFieldName + '.png'

    if (options.debug):
        print('  href: ', href)

    # Create the KML file

    if (options.debug):
        print('Writing KML to file: ', kmlPath)

    kml_file = open(kmlPath, 'w')

    kml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    kml_file.write('<kml xmlns="http://earth.google.com/kml/2.0">\n')
    kml_file.write('  <Document>\n')
    kml_file.write('    <name>' + catalog_name.upper() + ' radar images</name>\n')
    kml_file.write('    <open>1</open>\n')
    kml_file.write('    <Folder>\n')
    kml_file.write('     <name>' + platform + '</name>\n')
    kml_file.write('     <GroundOverlay>\n')
    kml_file.write('        <name>' + platform + '</name>\n')
    kml_file.write('        <Icon>\n')
    kml_file.write('          <href>' + href + '</href>\n')
    kml_file.write('          <refreshMode>onInterval</refreshMode>\n')
    kml_file.write('          <refreshInterval>120</refreshInterval>\n')
    kml_file.write('        </Icon>\n')
    kml_file.write('        <visibility>1</visibility>\n')
    kml_file.write('        <LatLonBox>\n')
    kml_file.write('          <north>' + north + '</north>\n')
    kml_file.write('          <south>' + south + '</south>\n')
    kml_file.write('          <east>' + east + '</east>\n')
    kml_file.write('          <west>' + west + '</west>\n')
    kml_file.write('        </LatLonBox>\n')
    kml_file.write('     </GroundOverlay>\n')
    kml_file.write('     </Folder>\n')
    kml_file.write('  </Document>\n')
    kml_file.write('</kml>\n')

    kml_file.close()

########################################################################
# Ftp the file

def ftpFile(incomingFilePath, catalogFileName):
    
    if (options.debug):
        print("==>> doing ftp <<==", file=sys.stderr)
        print("  incomingFilePath: ", incomingFilePath, file=sys.stderr)
        print("  catalogFileName: " + catalogFileName, file=sys.stderr)
        print("  to ftpDir: " + options.ftpDir, file=sys.stderr)

    # set ftp debug level

    if (options.debug):
        ftpDebugLevel = 2
    else:
        ftpDebugLevel = 0
    
    # open ftp connection
    
    ftp = ftplib.FTP(options.ftpServer, options.ftpUser, options.ftpPassword)
    ftp.set_debuglevel(ftpDebugLevel)
    
    # go to target dir

    if (options.debug):
        print("ftp cwd to: " + options.ftpDir, file=sys.stderr)
    
    ftp.cwd(options.ftpDir)
        
    # put the file

    fp = open(incomingFilePath, 'rb')
    ftp.storbinary('STOR ' + catalogFileName, fp)
    
    # close ftp connection
                
    ftp.quit()

    return

########################################################################
# Parse the command line

def parseArgs():
    
    global options

    # parse the command line

    usage = "usage: %prog [options]"
    parser = OptionParser(usage)

    # these options come from the ldata info file

    parser.add_option('--debug',
                      dest='debug', default='False',
                      action="store_true",
                      help='Set debugging on')

    parser.add_option('--unix_time',
                      dest='unixTime',
                      default=0,
                      help='Valid time for image')

    parser.add_option('--full_path',
                      dest='fullPath',
                      default='',
                      help='Full path of image file')

    parser.add_option('--file_name',
                      dest='fileName',
                      default='',
                      help='Name of image file')

    parser.add_option('--rel_file_path',
                      dest='relFilePath',
                      default='unknown',
                      help='Relative path of image file')

    parser.add_option('--catalog_name',
                      dest='catalogName',
                      default='wintre-mix',
                      help='Catalog name - i.e. project name')

    parser.add_option('--catalog_category',
                      dest='catalogCategory',
                      default='gis',
                      help='Outgoing category for the catalog')

    parser.add_option('--ftp_server',
                      dest='ftpServer',
                      default='catalog.eol.ucar.edu',
                      help='Target FTP server')

    parser.add_option('--ftp_user',
                      dest='ftpUser',
                      default='anonymous',
                      help='Target FTP user')

    parser.add_option('--ftp_password',
                      dest='ftpPassword',
                      default='',
                      help='Target FTP password')

    parser.add_option('--ftp_dir',
                      dest='ftpDir',
                      default='/pub/incoming/catalog/wintre-mix',
                      help='Target directory on the FTP server')

    parser.add_option('--temp_dir',
                      dest='tempDir',
                      default='/tmp/data/images',
                      help='Temporary directory for creating the KML file to send with the images.')
    (options, args) = parser.parse_args()

    if (options.debug):
        print("Options:", file=sys.stderr)
        print("  debug? ", options.debug, file=sys.stderr)
        print("  unixTime: ", options.unixTime, file=sys.stderr)
        print("  fullPath: ", options.fullPath, file=sys.stderr)
        print("  fileName: ", options.fileName, file=sys.stderr)
        print("  relFilePath: ", options.relFilePath, file=sys.stderr)
        print("  catalogName: ", options.catalogName, file=sys.stderr)
        print("  catalogCategory: ", options.catalogCategory, file=sys.stderr)
        print("  ftpServer: ", options.ftpServer, file=sys.stderr)
        print("  ftpUser: ", options.ftpUser, file=sys.stderr)
        print("  ftpPassword: ", options.ftpPassword, file=sys.stderr)
        print("  ftpDir: ", options.ftpDir, file=sys.stderr)
        print("  tempDir ", options.tempDir, file=sys.stderr)

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
