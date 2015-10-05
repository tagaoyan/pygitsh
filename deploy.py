#!/usr/bin/env python3

import os
import shutil
import logging

logging.basicConfig(format='%(levelname)-10s%(message)s', level=logging.INFO)
logger = logging.getLogger('pygitsh.deploy')
install_prefix = os.environ.get('HOME')

commands = [
    'alter',
    'backup',
    'create',
    'help',
    'list',
    'purge',
    'remove',
    'restore',
    'pygitsh.py',
]

tree = [
    ('git-shell-commands', commands),
    ('git-template', []),
    ('git-template/hooks', ['post-update']),
]

logger.info('install_prefix %s' % install_prefix)
try:
    if not os.path.isdir(install_prefix):
        raise ValueError("install_prefix %s is not a directory" % install_prefix)
    for dir, files in tree:
        os.makedirs(os.path.join(install_prefix, dir), exist_ok=True)
        logging.info('directory %s' % dir)
        for file in files:
            shutil.copy(file, os.path.join(install_prefix, dir))
            logger.info('file %s/%s' % (dir, file))
except Exception as e:
    logger.fatal(e)
    exit(1)
