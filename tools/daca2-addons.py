#!/usr/bin/python
#
# 1. Create a folder daca2-addons in your HOME folder
# 2. Put cppcheck-O2 in daca2-addons. It should be built with all optimisations.
# 3. Optional: Put a file called "suppressions.txt" in the daca2-addons folder.
# 4. Optional: tweak FTPSERVER and FTPPATH in this script below.
# 5. Run the daca2-addons script:  python daca2-addons.py FOLDER

import subprocess
import sys
import glob
import os
import datetime
import time
from daca2_lib import download_and_unpack, getpackages, removeAll

RESULTS_FILENAME = 'results.txt'


def dumpfiles(path):
    ret = []
    for g in glob.glob(path + '*'):
        if os.path.islink(g):
            continue
        if os.path.isdir(g):
            for df in dumpfiles(path + g + '/'):
                ret.append(df)
        elif os.path.isfile(g) and g[-5:] == '.dump':
            ret.append(g)
    return ret


def scanarchive(filepath, jobs):
    removeAll(exceptions=[RESULTS_FILENAME])

    download_and_unpack(filepath)

#
# List of skipped packages - which trigger known yet unresolved problems with cppcheck.
# The issues on trac (http://trac.cppcheck.net) are given for reference
# boost #3654 (?)
# flite #5975
# insight#5184
# valgrind #6151
# gcc-arm - no ticket. Reproducible timeout in daca2 though as of 1.73/early 2016.
#

    if filename[:5] == 'flite' or filename[:5] == 'boost' or filename[:7] == 'insight' or filename[:8] == 'valgrind' or filename[:7] == 'gcc-arm':
        results = open('results.txt', 'at')
        results.write('fixme: skipped package to avoid hang\n')
        results.close()
        return

    def keep_predicate(path):
        return os.path.splitext(path)[1] in ['.txt']
    removeLargeFiles('', keep_predicate)

    print('cppcheck ' + filename)

    p = subprocess.Popen(
        ['nice',
         '../cppcheck-O2',
         '--dump',
         '-D__GCC__',
         '--enable=style',
         '--error-exitcode=0',
         jobs,
         '.'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    comm = p.communicate()

    results = open('results.txt', 'at')

    addons = sorted(glob.glob(os.path.expanduser('~/cppcheck/addons/*.py')))
    for dumpfile in sorted(dumpfiles('')):
        for addon in addons:
            if addon.find('cppcheckdata.py') > 0:
                continue

            p2 = subprocess.Popen(['nice',
                                   'python',
                                   addon,
                                   dumpfile],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            comm = p2.communicate()
            results.write(comm[1])
    results.close()

FOLDER = None
JOBS = '-j1'
REV = None
for arg in sys.argv[1:]:
    if arg[:6] == '--rev=':
        REV = arg[6:]
    elif arg[:2] == '-j':
        JOBS = arg
    else:
        FOLDER = arg

if not FOLDER:
    print('no folder given')
    sys.exit(1)

archives = getpackages(FOLDER)
if len(archives) == 0:
    print('failed to load packages')
    sys.exit(1)

print('Sleep for 10 seconds..')
time.sleep(10)

workdir = os.path.expanduser('~/daca2/')

print('~/daca2/' + FOLDER)
if not os.path.isdir(workdir + FOLDER):
    os.makedirs(workdir + FOLDER)
os.chdir(workdir + FOLDER)

try:
    results = open('results.txt', 'wt')
    results.write('STARTDATE ' + str(datetime.date.today()) + '\n')
    if REV:
        results.write('GIT-REVISION ' + REV + '\n')
    results.write('\n')
    results.close()

    for archive in archives:
        scanarchive(archive, JOBS)

    results = open('results.txt', 'at')
    results.write('DATE ' + str(datetime.date.today()) + '\n')
    results.close()

except EOFError:
    pass

removeAll(exceptions=[RESULTS_FILENAME])
