# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Vinay M. Sajip. See LICENSE for licensing information.
#
# Part of the test harness for sarge: Subprocess Allegedly Rewards Good Encapsulation :-)
#
import sys
import time

def main(args=None):
    sys.stdout.write('Waiting ... ')
    sys.stdout.flush()
    if len(sys.argv) < 2:
        timeout = 5.0
    else:
        timeout = float(sys.argv[1])
    time.sleep(timeout)
    sys.stdout.write('done.\n')

if __name__ == '__main__':
    try:
        rc = main()
    except Exception as e:
        print(e)
        rc = 9
    sys.exit(rc)
