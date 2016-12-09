import glob
import logging
import os
import shutil
import subprocess
import time


DEBIAN = ['ftp://ftp.se.debian.org/debian/',
          'ftp://ftp.debian.org/debian/']


def wget(filepath):
    filename = filepath
    if filepath.find('/') >= 0:
        filename = filename[filename.rfind('/') + 1:]
    for d in DEBIAN:
        subprocess.call(
            ['nice', 'wget', '--tries=10', '--timeout=300', '-O', filename, d + filepath])
        if os.path.isfile(filename):
            return True
        print('Sleep for 10 seconds..')
        time.sleep(10)
    return False


def handleRemoveReadonly(func, path, exc):
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def getpackages(folder):
    if not wget('ls-lR.gz'):
        return []
    subprocess.call(['nice', 'gunzip', 'ls-lR.gz'])
    f = open('ls-lR', 'rt')
    lines = f.readlines()
    f.close()
    subprocess.call(['rm', 'ls-lR'])

    path = None
    archives = []
    filename = None
    for line in lines:
        line = line.strip()
        if len(line) < 4:
            if filename:
                archives.append(path + '/' + filename)
            path = None
            filename = None
        elif folder is None and line[:12] == './pool/main/':
            path = line[2:-1]
        elif folder and line[:13 + len(folder)] == './pool/main/' + folder + '/':
            path = line[2:-1]
        elif path and line.find('.orig.tar.') > 0:
            filename = line[1 + line.rfind(' '):]

    for a in archives:
        print(a)

    return archives


def download_and_unpack(filepath):
    logging.info(DEBIAN[0] + filepath)

    if not wget(filepath):
        if not wget(filepath):
            logging.error('wget failed at {}', filepath)
            return

    filename = filepath[filepath.rfind('/') + 1:]
    if filename[-3:] == '.gz':
        subprocess.call(['tar', 'xzvf', filename])
    elif filename[-3:] == '.xz':
        subprocess.call(['tar', 'xJvf', filename])
    elif filename[-4:] == '.bz2':
        subprocess.call(['tar', 'xjvf', filename])


def removeAll(exceptions=[]):
    filenames = []
    for g in glob.glob('[A-Za-z0-9]*'):
        filenames.append(g)
    for g in glob.glob('.[a-z]*'):
        filenames.append(g)

    for filename in filenames:
        count = 5
        while count > 0:
            count = count - 1

            try:
                if os.path.isdir(filename):
                    shutil.rmtree(filename, onerror=handleRemoveReadonly)
                elif filename not in exceptions:
                    os.remove(filename)
                break
            except WindowsError as err:
                time.sleep(30)
                if count == 0:
                    logging.error('Failed to cleanup {}: {}'.format(filename, err))
            except OSError as err:
                time.sleep(30)
                if count == 0:
                    logging.error('Failed to cleanup {}: {}'.format(filename, err))


def removeLargeFiles(path, keep_predicate):
    for g in glob.glob(path + '*'):
        if g == '.' or g == '..':
            continue
        if os.path.islink(g):
            continue
        if os.path.isdir(g):
            # Remove test code
            if g.endswith('/testsuite') or g.endswith('/clang/INPUTS'):
                shutil.rmtree(g, onerror=handleRemoveReadonly)
            else:
                removeLargeFiles(g + '/', keep_predicate)
        elif os.path.isfile(g) and not keep_predicate(g):
            statinfo = os.stat(g)
            if statinfo.st_size > 1000000:
                try:
                    os.remove(g)
                except OSError as err:
                    logging.error('Failed to remove {}: {}'.format(g, err))
