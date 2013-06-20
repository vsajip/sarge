# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Vinay M. Sajip. See LICENSE for licensing information.
#
# Part of the test harness for sarge: Subprocess Allegedly Rewards Good Encapsulation :-)
#
import sys

def main(args=None):
    while True:
        data = sys.stdin.readline()
        if not data:
            break
        data = data.strip()
        data = '%s %s\n' % (data, data)
        sys.stdout.write(data)
        sys.stdout.flush()

if __name__ == '__main__':
    try:
        rc = main()
    except Exception as e:
        print(e)
        rc = 9
    sys.exit(rc)
