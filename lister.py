# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Vinay M. Sajip. See LICENSE for licensing information.
#
# Part of the test harness for sarge: Subprocess Allegedly Rewards Good Encapsulation :-)
#
import logging
import optparse
import os
import re
import sys
import time

logger = logging.getLogger(__name__)

def _file_lines(fn):
    with open(fn) as f:
        for line in f:
            yield line

def _auto_lines():
    i = 1
    while True:
        line = 'line %d\n' % i
        i += 1
        yield line

def main(args=None):
    parser = optparse.OptionParser(usage='usage: %prog [options] [filename]',
                                   description='Print lines optionally from '
                                               'a file, with a delay between '
                                               'lines. If no filename is '
                                               'specified, lines of the form '
                                               '"line N" are generated '
                                               'internally and printed.')
    parser.add_option('-d', '--delay', default=None, type=float,
                      help='Delay between lines (seconds)')
    parser.add_option('-c', '--count', default=0, type=int,
                      help='Maximum number of lines to output')
    parser.add_option('-i', '--interest', default=None,
                      help='Indicate patterns of interest for logging')
    if args is None:
        args = sys.argv[1:]
    options, args = parser.parse_args(args)
    if not args:
        liner = _auto_lines()
    else:
        fn = args[0]
        if not os.path.isfile(fn):
            sys.stderr.write('not a file: %r\n' % fn)
            return 2
        liner = _file_lines(fn)
    bytes_written = 0
    pattern = options.interest
    if pattern:
        pattern = re.compile(pattern)
    nlines = 0
    for line in liner:
        sys.stdout.write(line)
        sys.stdout.flush()
        nlines += 1
        bytes_written += len(line)
        if pattern and pattern.search(line):
            s = ': %r' % line
            level = logging.INFO
        else:
            s = ''
            level = logging.DEBUG
        logger.log(level, 'Wrote out %d bytes%s', bytes_written, s)
        if options.count and nlines >= options.count:
            break
        if options.delay:
            time.sleep(options.delay)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename='lister.log',
                        filemode='w', format='%(asctime)s %(levelname)s %(message)s')
    try:
        rc = main()
    except Exception as e:
        print(e)
        rc = 9
    sys.exit(rc)
