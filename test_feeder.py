# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2021 Vinay M. Sajip. See LICENSE for licensing information.
#
# Part of the test harness for sarge: Subprocess Allegedly Rewards Good Encapsulation :-)
#
import sys
import time

import sarge

try:
    text_type = unicode
except NameError:
    text_type = str


def main(args=None):
    feeder = sarge.Feeder()
    p = sarge.run([sys.executable, 'echoer.py'], input=feeder, async_=True)
    try:
        lines = ('hello', 'goodbye')
        gen = iter(lines)
        while p.commands[0].returncode is None:
            try:
                data = next(gen)
            except StopIteration:
                break
            feeder.feed(data + '\n')
            p.commands[0].poll()
            time.sleep(0.05)  # wait for child to return echo
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
