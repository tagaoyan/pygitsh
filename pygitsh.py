"""
helper functions for pygitsh

Glossary
    repository  a form of git data storage

    repository name
            the name of a repository

    repository directory
            1. the directory containing the repository, usually with a name
            ending with ".git"

            2. the name of a repository directory

    backup  the action or result of packing the repository directory
            elsewhere

    backup archive
            1. the archive storing the backup
            2. the name of a backup archive

Logging Levels
    This program uses these logging levels.

    DEBUG   giving debug information

    INFO    giving information of what is done

            This is the default level

    WARNING giving warning of actions not recommended

    ERROR   giving error message not severe enough to bring the program down

    CRITICAL
            state the failure of running which must be terminated instantly

External Commands
    These commands are requires.

    * git (from git)
    * rm, tar, mv, touch (from coreutils or busybox)
"""

__author__ = 'Yan Gao <tagaoyan@gmail.com>'
__date__ = 'Oct 5, 2015'
__version__ = '1.0.0'
__credits__ = '''I used to use shell do the same thing, but it is too ugly.
So I use python.  '''

# Handling external command call

import subprocess
from functools import wraps

def call(cmd):
    '''
    run `cmd` in a subprocess and return the state

    Exceptions is not handled
    '''
    return subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def output(cmd):
    '''
    run `cmd` in a subprocess and return the output

    Exceptions is not handled
    '''
    return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, universal_newlines=True).strip()

def exit_handler(retcode=None):
    '''
    exit with `retcode` if any exception is raised

    if `retcode` is None, return a code ranging from 128 to 255
    '''
    def exit_decor(action):
        @wraps(action)
        def run_act_or_exit(*args, **kwargs):
            try:
                return action(*args, **kwargs)
            except Exception as e:
                ecls = e.__class__
                ret = retcode or hash(action) % 128 + 128
                logger.fatal('cannot continue with %s.%s%s in %s' % (ecls.__module__, ecls.__name__, e.args, action.__name__))
                quit(ret)
        return run_act_or_exit
    return exit_decor

def none_handler(value=None):
    '''
    return `value` if any exception is raised.
    '''
    def none_decor(action):
        @wraps(action)
        def run_act_or_none(*args, **kwargs):
            try:
                return action(*args, **kwargs)
            except Exception:
                logger.debug('use %s instead for the return %s()' % (value, action.__name__))
                return value
        run_act_or_none.__doc__ = action.__doc__
        return run_act_or_none
    return none_decor


# Logging

import logging
logging.basicConfig(format='%(levelname)-10s%(message)s', level=logging.INFO)
logger = logging.getLogger('pygitsh')

def quit(state):
    '''
    exit with `state` after giving the information
    '''
    logger.info('exit with %#x' % state)
    exit(state)

# locating repos

SUF_GIT='.git'
LEN_GIT=len(SUF_GIT)
SUF_BACKUP='.backup.tar.bz2'
LEN_BACKUP=len(SUF_BACKUP)

def compatible_name(f):
    '''
    make functions accepting filename also accepts repository name

    With this decorator, f('foo') works the same as f("foo.git")
    '''
    @wraps(f)
    def compatible_func(name, *args, **kwargs):
        if name.endswith(SUF_GIT):
            return f(name, *args, **kwargs)
        else:
            return f(name + SUF_GIT, *args, **kwargs)
    compatible_func.__doc__ = f.__doc__
    return compatible_func

def repo_name(filename):
    '''
    return the name of a repository directory `filename` or a backup archive
    '''
    if filename.endswith(SUF_GIT):
        return filename[:-LEN_GIT]
    elif filename.endswith(SUF_BACKUP):
        return filename[:-LEN_BACKUP]
    else:
        return filename

from glob import glob
import os

def find_repos(prefix=''):
    '''
    return a list of repository directories begining with `prefix`
    '''
    repos = [x for x in glob(prefix + '*' + SUF_GIT) if os.path.isdir(x)]
    if not repos:
        logger.info('no repository found')
    return repos

def find_backups(prefix=''):
    '''
    return a list of backup archives

    If `prefix` is specified, only return repositories begining with prefix + '.'
    '''
    if not prefix:
        backs = glob('*' + SUF_BACKUP)
    else:
        backs = glob(prefix + '.*' + SUF_BACKUP)
    if not backs:
        logger.info('no backup found')
    return backs

@compatible_name
def repo_exists(filename):
    '''
    return whether repository directory `filename` exists
    '''
    return os.path.isdir(filename)


@compatible_name
@exit_handler()
def create_repo(filename):
    '''
    create a repository in directory `filename`
    '''
    call(['git', 'init', '--bare', filename])
    logger.info('new repository directory "%s" created' % filename)

@compatible_name
@exit_handler()
def create_repo_from_uri(filename, uri):
    '''
    clone `uri` to repository directory `filename`
    '''
    call(['git', 'clone', '--bare', uri, filename])
    logger.info('cloned "%s" to repository directory "%s"' % (uri, filename))

@compatible_name
@exit_handler()
def remove_repo(filename):
    '''
    remove repository directory `filename`
    '''
    call(['rm', '-rf', filename])
    logger.info('repository directory "%s" removed' % filename)

@compatible_name
@exit_handler()
def rename_repo(filename, newname):
    '''
    rename repository directory `filename` to `newname` + ".git"
    '''
    call(['mv', filename, newname + SUF_GIT])
    logger.info('repository directory "%s" renamed to "%s"' % (filename, newname + SUF_GIT))

import time

@compatible_name
@exit_handler()
def backup_repo(filename):
    '''
    backup a repository directory `filename`

    The name of the backup archive begins with repository name and
    UNIX time stamp separated by ".".
    '''
    backfname = repo_name(filename) + time.strftime('.%s') + SUF_BACKUP
    call(['tar', '-cjf', backfname, filename])
    logger.info('repository directory "%s" backuped as "%s"' % (filename, backfname))

@exit_handler()
def restore_repo(backfname):
    '''
    restore repository from backup archive `backfname`
    '''
    call(['tar', '-xjf', backfname])
    logger.info('restored from backup archive "%s"' % backfname)

@exit_handler()
def remove_backup(backfname):
    '''
    remove backup archive `backfname`
    '''
    call(['rm', '-f', backfname])
    logger.info('backup archive "%s" removed' % backfname)

@compatible_name
@exit_handler()
def set_repo_description(filename, descr):
    '''
    set the description of repository directory `fileneme` to `descr`
    '''
    call(['git', '--git-dir=%s' % filename, 'config', 'gitweb.description', descr])
    logger.info('repository directory "%s": description="%s"' % (filename, descr))

@none_handler('<UNKNOWN>')
def repo_description(filename):
    '''
    return the description of repository directory `filename`
    '''
    return output(['git', '--git-dir=%s' % filename, 'config', 'gitweb.description'])

@compatible_name
@exit_handler()
def set_repo_owner(filename, owner):
    '''
    set the owner of repository directory `fileneme` to `owner`
    '''
    call(['git', '--git-dir=%s' % filename, 'config', 'gitweb.owner', owner])
    logger.info('repository directory "%s": owner="%s"' % (filename, owner))

@compatible_name
@none_handler('<UNKNOWN>')
def repo_owner(filename):
    '''
    return the owner of repository directory `filename`
    '''
    return output(['git', '--git-dir=%s' % filename, 'config', 'gitweb.owner'])

@compatible_name
@exit_handler()
def set_repo_private(filename, state):
    '''
    set whether the repository directory `filename` is private
    '''
    if state:
        call(['touch', '%s/git-daemon-export-ok' % filename])
    else:
        call(['rm', '-rf', '%s/git-daemon-export-ok' % filename])
    logger.info('repository directory "%s": private="%s"' % (filename, state))

def repo_private(filename):
    '''
    return whether the repository directory `filename` is private
    '''
    return os.path.exists('%s/git-daemon-export-ok' % filename)

