# -*- coding: utf-8 -*-
"""
Adapted from http://code.activestate.com/recipes/577334/

by László Nagy, released under the MIT license.
"""

import os
import sys
import threading
import time
import traceback

def _get_stack_traces():
    code = []
    threads = dict((t.ident, t.name) for t in threading.enumerate())
    for threadId, stack in sys._current_frames().items():
        if threadId == threading.current_thread().ident:
            continue
        threadName = threads.get(threadId, 'Unknown')
        code.append('\n# Thread: %s (%s)' % (threadId, threadName))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: %r, line %d, in %s' % (filename, lineno, name))
            if line:
                code.append('  %s' % (line.strip()))

    return '\n'.join(code)


class TraceDumper(threading.Thread):
    """Dump stack traces into a given file periodically."""

    def __init__(self, path, interval):
        """
        @param path: File path to output stack trace info.
        @param interval: in seconds - how often to update the trace file.
        """
        assert(interval > 0.1)
        self.interval = interval
        self.path = os.path.abspath(path)
        self.stop_requested = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        while not self.stop_requested.isSet():
            time.sleep(self.interval)
            self.write_stack_traces()

    def stop(self):
        self.stop_requested.set()
        self.join()

    def write_stack_traces(self):
        with open(self.path, 'w') as out:
            out.write(_get_stack_traces())


_tracer = None

def start_trace(path, interval=5):
    """Start tracing into the given file."""
    global _tracer
    if _tracer is None:
        _tracer = TraceDumper(path, interval)
        _tracer.daemon = True
        _tracer.start()
    else:
        raise Exception('Already tracing to %s' % _tracer.path)


def stop_trace():
    """Stop tracing."""
    global _tracer
    if _tracer is not None:
        _tracer.stop()
        _tracer = None
