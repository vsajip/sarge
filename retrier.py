#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 Red Dove Consultants Limited
#
import argparse
import logging
import os
import subprocess
import sys
import time

DEBUGGING = 'PY_DEBUG' in os.environ

logger = logging.getLogger(__name__)


def main():
    fn = os.path.basename(__file__)
    fn = os.path.splitext(fn)[0]
    lfn = os.path.expanduser('~/logs/%s.log' % fn)
    if os.path.isdir(os.path.dirname(lfn)):
        logging.basicConfig(level=logging.DEBUG, filename=lfn, filemode='w',
                            format='%(message)s')
    adhf = argparse.ArgumentDefaultsHelpFormatter
    ap = argparse.ArgumentParser(formatter_class=adhf, prog=fn)
    aa = ap.add_argument
    aa('-r', '--retries', default=3, type=int, help='Number of times to retry')
    aa('-d', '--delay', default=5, type=int, help='Number of seconds to delay between retries')
    options, args = ap.parse_known_args()
    rc = 1
    while options.retries > 0:
        p = subprocess.Popen(args)
        p.wait()
        if p.returncode == 0:
            rc = 0
            break
        options.retries -= 1
        if options.delay:
            time.sleep(options.delay)
    return rc

if __name__ == '__main__':
    try:
        rc = main()
    except KeyboardInterrupt:
        rc = 2
    except Exception as e:
        if DEBUGGING:
            s = ' %s:' % type(e).__name__
        else:
            s = ''
        sys.stderr.write('Failed:%s %s\n' % (s, e))
        if DEBUGGING: import traceback; traceback.print_exc()
        rc = 1
    sys.exit(rc)
