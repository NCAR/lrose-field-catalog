#!/usr/bin/env python

#=====================================================================
#
# Download Mendoza radar files from ftp site
#
#=====================================================================

from __future__ import print_function
import os
import sys
import time
import datetime
from datetime import timedelta
import string
import ftplib
import subprocess
from optparse import OptionParser

def main():

    global options
    global ftpUser
    global ftpPassword
    global ftpDebugLevel
    global tmpDir

    global thisScriptName
    thisScriptName = os.path.basename(__file__)

    # parse the command line

    parseArgs()

    # initialize
    
    beginString = "BEGIN: " + thisScriptName
    today = datetime.datetime.now()
    beginString += " at " + str(today)
    
    if (options.force):
        beginString += " (ftp forced)"

    print("=========================================================")
    print(beginString)
    print("=========================================================")

    # set full paths for targetDir and tmpDir and sourceDir

    options.tmpDir = options.tmpDir + '/' + options.radar 
    options.targetDir = options.targetDir + '/' + options.radar 
    if (options.radar == 'dowc'):
        options.radar = 'cow1'
    options.sourceDir = '/' + options.radar + options.sourceDir

    # create tmp dir if necessary

    try:
        os.makedirs(options.tmpDir)
    except OSError as exc:
        if (options.verbose):
            print("WARNING: cannot make tmp dir: ", options.tmpDir, file=sys.stderr)
            print("  ", exc, file=sys.stderr)
            
    # set ftp debug level

    if (options.verbose):
        ftpDebugLevel = 2
    elif (options.debug):
        ftpDebugLevel = 1
    else:
        ftpDebugLevel = 0
    
    # get current date and time

    nowTime = time.gmtime()
    now = datetime.datetime(nowTime.tm_year, nowTime.tm_mon, nowTime.tm_mday,
                            nowTime.tm_hour, nowTime.tm_min, nowTime.tm_sec)
    nowDateStr = now.strftime("%Y%m%d")
    nowDateTimeStr = now.strftime("%Y%m%d%H%M%S")

    # compute start time

    pastSecs = int(options.pastSecs)
    pastDelta = timedelta(0, pastSecs)
    startTime = now - pastDelta
    startDateTimeStr = startTime.strftime("%Y%m%d%H%M%S")
    startDateStr = startTime.strftime("%Y%m%d")

    # set up list of days to be checked

    nDays = int((pastSecs / 86400) + 1)
    dateStrList = []
    for iDay in range(0, nDays):
        deltaSecs = timedelta(0, iDay * 86400)
        dayTime = now - deltaSecs
        dateStr = dayTime.strftime("%Y%m%d")
        dateStrList.append(dateStr)

    # debug print

    if (options.debug):
        print("  time now: ", nowDateTimeStr, file=sys.stderr)
        print("  getting data after: ", startDateTimeStr, file=sys.stderr)
        print("  nDays: ", nDays, file=sys.stderr)
        print("  dateStrList: ", dateStrList, file=sys.stderr)

    if (options.skipFtp):
        print("skipping FTP of", options.sourceDir, " to", options.targetDir)
        sys.exit(0)

    # open ftp connection
    
    ftp = ftplib.FTP(options.ftpServer, options.ftpUser, options.ftpPasswd)
    ftp.set_debuglevel(ftpDebugLevel)

    # got to radar directory on the ftp site

    ftp.cwd(options.sourceDir)
    ftpDateList = ftp.nlst()
    ftpDates = [filename[6:14] for filename in ftpDateList]

    # loop through days

    count = 0
    for dateStr in dateStrList:

        if (dateStr not in ftpDates):
            if (options.verbose):
                print("WARNING: ignoring date, does not exist on ftp site", file=sys.stderr)
                print("  dateStr: ", dateStr, file=sys.stderr)
            continue

        # make the target directory

        localDayDir = os.path.join(options.targetDir, dateStr)
        try:
            os.makedirs(localDayDir)
        except OSError as exc:
            if (options.verbose):
                print("WARNING: trying to create dir: ", localDayDir, file=sys.stderr)
                print("  ", exc, file=sys.stderr)
        os.chdir(localDayDir)

        # get local file list - i.e. those which have already been downloaded

        localFileList = os.listdir('.')
        localFileList.reverse()
        if (options.verbose):
            print("  localFileList: ", localFileList, file=sys.stderr)
            
        # get ftp server file list, for day dir
        
        ftpFileList = ftp.nlst()
        ftpFileList.reverse()
        if (options.verbose):
            print("  ftpFileList: ", ftpFileList, file=sys.stderr)

        # loop through the ftp file list, downloading those that have
        # not yet been downloaded and those for correct date and start
        # with cfrad in filename

        for ftpFileName in ftpFileList:

            count = 0
            fileDate = ftpFileName[6:14]

            if (ftpFileName not in localFileList and ftpFileName[0:5] == 'cfrad' and fileDate == dateStr):
                downloadFile(ftp, dateStr, ftpFileName)
                count = count + 1
                    
    # close ftp connection
    
    ftp.quit()

    print("===============================================================")
    print("END: " + thisScriptName + str(datetime.datetime.now()))
    print("===============================================================")

    sys.exit(0)

########################################################################
# Download a file into the current directory

def downloadFile(ftp, dateStr, fileName):
    
    if (options.debug):
        print("  downloading file: ", fileName, file=sys.stderr)
        
    # get file, store in tmp

    tmpPath = os.path.join(options.tmpDir, fileName)

    if (options.verbose):
        print("retrieving file, storing as tmpPath: ", tmpPath, file=sys.stderr)
    ftp.retrbinary('RETR '+ fileName, open(tmpPath, 'wb').write)

    # move to final location - i.e. this directory
    
    cmd = "mv " + tmpPath + " ."
    runCommand(cmd)

    # write latest_data_info
    
    fileTimeStr = fileName[15:21]
    fileDateTimeStr = dateStr + fileTimeStr
    
    relPath = os.path.join(dateStr, fileName)
    cmd = "/home/rsfdata/lrose/bin/LdataWriter -dir " + options.targetDir \
          + " -rpath " + relPath \
          + " -ltime " + fileDateTimeStr \
          + " -writer " + thisScriptName \
          + " -dtype mdv"
    if (options.verbose):
        print("LdataWriter cmd: ", cmd, file=sys.stderr)
    runCommand(cmd)

########################################################################
# Parse the command line

def parseArgs():
    
    global options

    # parse the command line

    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option('--debug',
                      dest='debug', default=False,
                      action="store_true",
                      help='Set debugging on')
    parser.add_option('--verbose',
                      dest='verbose', default=False,
                      action="store_true",
                      help='Set verbose debugging on')
    parser.add_option('--force',
                      dest='force', default=False,
                      action="store_true",
                      help='Force ftp transfer')
    parser.add_option('--skipFtp',
                      dest='skipFtp', default=False,
                      action="store_true",
                      help='Skip ftp access for debugging')
    parser.add_option('--ftpServer',
                      dest='ftpServer',
                      default='codewx.io',
                      help='Name of ftp server host')
    parser.add_option('--ftpUser',
                      dest='ftpUser',
                      default='ncar-barn@codewx.io',
                      help='User for ftp host')
    parser.add_option('--ftpPasswd',
                      dest='ftpPasswd',
                      default='Mix3dPh4se',
                      help='Passwd for ftp host')
    parser.add_option('--sourceDir',
                      dest='sourceDir',
                      default='/data',
                      help='Path of source directory')
    parser.add_option('--targetDir',
                      dest='targetDir',
                      default='/scr/snow1/rsfdata/projects/lee/cfradial',
                      help='Path of target directory')
    parser.add_option('--tmpDir',
                      dest='tmpDir',
                      default='/scr/snow1/rsfdata/projects/lee/cfradial/incoming',
                      help='Path of tmp directory')
    parser.add_option('--pastSecs',
                      dest='pastSecs',
                      default=3600,
                      help='How far back to retrieve (secs)')
    parser.add_option('--radar',
                      dest='radar',
                      default='dow6',
                      help='Which radar dow6, dow7, dow8, cow1')

    (options, args) = parser.parse_args()

    if (options.verbose):
        options.debug = True

    if (options.debug):
        print("Options:", file=sys.stderr)
        print("  debug? ", options.debug, file=sys.stderr)
        print("  force? ", options.force, file=sys.stderr)
        print("  skipFtp? ", options.skipFtp, file=sys.stderr)
        print("  ftpServer: ", options.ftpServer, file=sys.stderr)
        print("  ftpUser: ", options.ftpUser, file=sys.stderr)
        print("  sourceDir: ", options.sourceDir, file=sys.stderr)
        print("  tmpDir: ", options.tmpDir, file=sys.stderr)
        print("  pastSecs: ", options.pastSecs, file=sys.stderr)

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
