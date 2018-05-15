import optparse # because of 2.6 support
import sys
import threading
import time
import logging

from sarge import capture_stdout, run, Capture

logger = logging.getLogger(__name__)

def progress(capture, options):
    lines_seen = 0
    messages = {
        b'line 25\n': 'Getting going ...\n',
        b'line 50\n': 'Well on the way ...\n',
        b'line 75\n': 'Almost there ...\n',
    }
    while True:
        s = capture.readline(timeout=1.0)
        if not s:
            logger.debug('No more data, breaking out')
            break
        if options.dots:
            sys.stderr.write('.')
            sys.stderr.flush()  # needed for Python 3.x
        else:
            msg = messages.get(s)
            if msg:
                sys.stderr.write(msg)
        lines_seen += 1
    if options.dots:
        sys.stderr.write('\n')
    sys.stderr.write('Done - %d lines seen.\n' % lines_seen)

def main():
    parser = optparse.OptionParser()
    parser.add_option('-n', '--no-dots', dest='dots', default=True,
                      action='store_false', help='Show dots for progress')
    options, args = parser.parse_args()

    #~ p = capture_stdout('ncat -k -l -p 42421', async_=True)
    p = capture_stdout('python lister.py -d 0.1 -c 100', async_=True)

    time.sleep(0.01)
    t = threading.Thread(target=progress, args=(p.stdout, options))
    t.start()

    while(p.returncodes[0] is None):
        # We could do other useful work here. If we have no useful
        # work to do here, we can call readline() and process it
        # directly in this loop, instead of creating a thread to do it in.
        p.commands[0].poll()
        time.sleep(0.05)
    t.join()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, filename='test_progress.log',
                        filemode='w', format='%(asctime)s %(threadName)-10s %(name)-15s %(lineno)4d %(message)s')
    sys.exit(main())
