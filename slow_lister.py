import logging
import os
import sys
import time

logger = logging.getLogger(__name__)

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    if not args:
        sys.stderr.write('usage: slow_lister <filename>\n')
        return 1
    fn = args[0]
    if not os.path.isfile(fn):
        sys.stderr.write('not a file: %r\n' % fn)
        return 2
    bytes_written = 0
    with open(fn) as f:
        for line in f:
            sys.stdout.write(line)
            sys.stdout.flush()
            bytes_written += len(line)
            if '<head>' in line or '<body>' in line:
                s = ': %r' % line
                level = logging.INFO
            else:
                s = ''
                level = logging.DEBUG
            logger.log(level, 'Wrote out %d bytes%s', bytes_written, s)
            time.sleep(0.25)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, filename='slow_lister.log',
                        filemode='w', format='%(asctime)s %(message)s')
    try:
        rc = main()
    except Exception as e:
        print(e)
        rc = 9
    sys.exit(rc)
