#!/usr/bin/env python

# ========================================================================== #
#
# Configure the host for field catalog project
#
# ========================================================================== #

from __future__ import print_function
import os
import sys
from optparse import OptionParser
import datetime
import subprocess
import string

def main():

    global options

    homeDir = os.environ['HOME']
    projDir = os.path.join(homeDir, 'projDir')
    controlDir = os.path.join(projDir, 'control')
    defaultGitDir = os.path.join(homeDir, "git/lrose-field-catalog")

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
    parser.add_option('--gitDir',
                      dest='gitDir', default=defaultGitDir,
                      help='Path of main directory in git')
    (options, args) = parser.parse_args()
    
    if (options.verbose):
        options.debug = True

    # compute paths

    gitProjDir = os.path.join(options.gitDir, 'projDir')
    gitSystemDir = os.path.join(gitProjDir, 'system')
    
    # debug print

    if (options.debug):
        print("Running script: ", os.path.basename(__file__), file=sys.stderr)
        print("", file=sys.stderr)
        print("  Options:", file=sys.stderr)
        print("    Debug: ", options.debug, file=sys.stderr)
        print("    Verbose: ", options.verbose, file=sys.stderr)
        print("    homeDir: ", homeDir, file=sys.stderr)
        print("    projDir: ", projDir, file=sys.stderr)
        print("    controlDir: ", controlDir, file=sys.stderr)
        print("    gitDir: ", options.gitDir, file=sys.stderr)
        print("    gitProjDir: ", gitProjDir, file=sys.stderr)
        print("    gitSystemDir: ", gitSystemDir, file=sys.stderr)
        
    # banner

    print(" ")
    print("*********************************************************************")
    print()
    print("  configure project")
    print()
    print("  runtime: " + str(datetime.datetime.now()))
    print()
    print("*********************************************************************")
    print(" ")

    # make links to the dotfiles in git projDir
    
    os.chdir(homeDir)
    for rootName in ['cshrc', 'emacs', 'Xdefaults' ]:
        dotName = '.' + rootName
        removeSymlink(homeDir, dotName)
        sourceDir = os.path.join(gitSystemDir, 'dotfiles')
        sourcePath = os.path.join(sourceDir, rootName)
        cmd = "ln -s " + sourcePath + " " + dotName
        runCommand(cmd)

    # make link to projDir

    removeSymlink(homeDir, 'projDir')
    os.chdir(homeDir)
    cmd = "ln -s " + gitProjDir
    runCommand(cmd)
    
    # create symlink to logs

    #os.chdir(projDir)
    #removeSymlink(projDir, "logs")
    #if (os.path.exists('logs') == False):
    #    cmd = "ln -s data/logs"
    #    runCommand(cmd)

    # done

    sys.exit(0)
    
########################################################################
# Remove a symbolic link
# Exit on error

def removeSymlink(dir, linkName):

    os.chdir(dir)

    # remove if exists
    if (os.path.islink(linkName)):
        os.unlink(linkName)
        return

    if (os.path.exists(linkName)):
        # link name exists but is not a link
        print("ERROR - trying to remove symbolic link", file=sys.stderr)
        print("  dir: ", dir, file=sys.stderr)
        print("  linkName: ", linkName, file=sys.stderr)
        print("This is NOT A LINK", file=sys.stderr)
        sys.exit(1)

########################################################################
# Run a command in a shell, wait for it to complete

def runCommand(cmd):

    if (options.debug == True):
        print("running cmd:",cmd, file=sys.stderr)

    try:
        retcode = subprocess.call(cmd, shell=True)
        if retcode < 0:
            print("Child was terminated by signal: ", -retcode, file=sys.stderr)
        else:
            if (options.verbose == True):
                print("Child returned code: ", retcode, file=sys.stderr)
    except OSError as e:
        print("Execution failed:", e, file=sys.stderr)

########################################################################
# Run - entry point

if __name__ == "__main__":
   main()
