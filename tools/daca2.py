#!/usr/bin/python
#
# 1. Create a folder daca2 in your HOME folder
# 2. Put cppcheck-O2 in daca2. It should be built with all optimisations.
# 3. Optional: Put a file called "suppressions.txt" in the daca2 folder.
# 4. Optional: tweak FTPSERVER and FTPPATH in this script below.
# 5. Run the daca2 script:  python daca2.py FOLDER

import argparse
import subprocess
import sys
import datetime
import os
import logging

from daca2_lib import download_and_unpack, getpackages, removeLargeFiles
from daca2_lib import removeAll

RESULTS_FILENAME = 'results.txt'


def strfCurrTime(fmt):
    return datetime.time.strftime(datetime.datetime.now().time(), fmt)


def scanarchive(filepath, jobs, cpulimit):
    removeAll(exceptions=[RESULTS_FILENAME])
    download_and_unpack(filepath)

    def keep_predicate(path):
        return os.path.splitext(path)[1] in ['.txt']
    removeLargeFiles('', keep_predicate)

    filename = filepath[filepath.rfind('/') + 1:]
    print(strfCurrTime('[%H:%M] cppcheck ') + filename)

    if cpulimit:
        cmd = 'cpulimit --limit=' + cpulimit
    else:
        cmd = 'nice --adjustment=1000'
    cmd = cmd + ' ../cppcheck-O2 -D__GCC__ --enable=style --inconclusive --error-exitcode=0 --exception-handling=stderr ' + jobs + ' .'
    cmds = cmd.split()
    cmds.append('--template={callstack}: ({severity}) {message} [{id}]')

    p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    comm = p.communicate()

    if p.returncode == 0:
        logging.info(comm[1] + strfCurrTime('[%H:%M]'))
    elif comm[0].find('cppcheck: error: could not find or open any of the paths given.') < 0:
        logging.error(comm[1] + strfCurrTime('[%H:%M]'))
        logging.error('Exit code is not zero! Crash?\n')


parser = argparse.ArgumentParser(description='Checks debian source code')
parser.add_argument('folder', metavar='FOLDER')
parser.add_argument('--rev')
parser.add_argument('--workdir', default='~/daca2')
parser.add_argument('-j', '--jobs', default='-j1')
parser.add_argument('--skip', default=[], action='append')
parser.add_argument('--cpulimit')

args = parser.parse_args()

workdir = os.path.expanduser(args.workdir)
if not os.path.isdir(workdir):
    print('workdir \'' + workdir + '\' is not a folder')
    sys.exit(1)

workdir = os.path.join(workdir, args.folder)
if not os.path.isdir(workdir):
    os.makedirs(workdir)

RESULTS_FILE = os.path.join(workdir, RESULTS_FILENAME)

logging.basicConfig(
        filename=RESULTS_FILE,
        level=logging.INFO,
        format='%(message)s')

print(workdir)

archives = getpackages(args.folder)
if len(archives) == 0:
    logging.critical('failed to load packages')
    sys.exit(1)

if not os.path.isdir(workdir):
    os.makedirs(workdir)
os.chdir(workdir)

try:
    logging.info('STARTDATE ' + str(datetime.date.today()))
    logging.info('STARTTIME ' + strfCurrTime('%H:%M:%S'))
    if args.rev:
        logging.info('GIT-REVISION ' + args.rev + '\n')
    logging.info('')

    for archive in archives:
        if len(args.skip) > 0:
            a = archive[:archive.rfind('/')]
            a = a[a.rfind('/')+1:]
            if a in args.skip:
                continue
        scanarchive(archive, args.jobs, args.cpulimit)

    logging.info('DATE {}'.format(datetime.date.today()))
    logging.info('TIME {}'.format(strfCurrTime('%H:%M:%S')))

except EOFError:
    pass

removeAll(exceptions=[RESULTS_FILENAME])
