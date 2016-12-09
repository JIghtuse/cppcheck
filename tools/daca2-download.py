#!/usr/bin/python
#
# Downloads all daca2 source code packages.
#
# Usage:
# $ mkdir ~/daca2-packages && python daca2-download.py


import subprocess
import sys
import glob
import os
import time
from daca2_lib import download_and_unpack, getpackages, removeAll
from daca2_lib import removeLargeFiles

SOURCE_EXTENSIONS = ['.C', '.c', '.cc', '.cpp', '.cxx', '.h', '.H', '.c++',
                     '.hpp', '.tpp', '.t++']


def downloadpackage(filepath, outpath):
    removeAll()
    download_and_unpack(filepath)

    def keep_predicate(path):
        return os.path.splitext(path)[1] in SOURCE_EXTENSIONS
    removeLargeFiles('', keep_predicate)

    filename = filepath[filepath.rfind('/') + 1:]

    for g in glob.glob('[#_A-Za-z0-9]*'):
        if os.path.isdir(g):
            subprocess.call(['tar', '-cJvf', outpath + filename[:filename.rfind('.')] + '.xz', g])
            break

workdir = os.path.expanduser('~/daca2-packages/tmp/')
if not os.path.isdir(workdir):
    os.makedirs(workdir)
os.chdir(workdir)

packages = getpackages(None)
if len(packages) == 0:
    print('failed to load packages')
    sys.exit(1)

print('Sleep for 10 seconds..')
time.sleep(10)

for package in packages:
    downloadpackage(package, os.path.expanduser('~/daca2-packages/'))

removeAll()
