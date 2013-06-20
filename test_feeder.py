# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Vinay M. Sajip. See LICENSE for licensing information.
#
# Part of the test harness for sarge: Subprocess Allegedly Rewards Good Encapsulation :-)
#
import os
import subprocess
import sys
import time

import sarge

try:
    text_type = unicode
except NameError:
    text_type = str
    raw_input = input

class Feeder(object):
    def __init__(self):
        self._r, self._w = os.pipe()

    def fileno(self):
        return self._r

    def feed(self, data):
        if isinstance(data, text_type):
            data = data.encode('utf-8')
        if not isinstance(data, bytes):
            raise TypeError('Bytes expected, got %s' % type(data))
        os.write(self._w, data)

    def close(self):
        os.close(self._r)
        os.close(self._w)

def main(args=None):
    feeder = Feeder()
    p = sarge.run([sys.executable, 'echoer.py'], input=feeder, async=True)
    try:
        lines = ('hello', 'goodbye')
        gen = iter(lines)
        while p.commands[0].returncode is None:
            data = next(gen)
            feeder.feed(data + '\n')
            p.commands[0].poll()
            time.sleep(0.05)    # wait for child to return echo
    finally:
        p.commands[0].terminate()
        feeder.close()

if __name__ == '__main__':
    try:
        rc = main()
    except Exception as e:
        print(e)
        rc = 9
    sys.exit(rc)
