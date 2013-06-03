import logging
from sarge import run, Capture
import time

logger = logging.getLogger(__name__)

logging.basicConfig(filename='test_expect.log', filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(name)s %(threadName)s %(lineno)4d %(message)s')
cap = Capture(buffer_size=-1)   # line buffered
p = run('python lister.py -d 0.01', async=True,
        stdout=cap)

WAIT_TIME = 1.0

def do_expect(pattern, timeout=None):
    stime = time.time()
    cap.expect(pattern, timeout or WAIT_TIME)
    elapsed = time.time() - stime
    if not cap.match:
        print('%r not found within time limit.' % pattern)
        result = False
    else:
        print('%r found at %s in %.1f seconds.' % (pattern, cap.match.span(),
                                                   elapsed))
        result = True
    return result

if do_expect('line 1$'):
    if do_expect('line 5$'):
        if do_expect('line 1.*$'):
            cap.close(True)
            print(cap.bytes[cap.match.start():cap.match.end()])

p.commands[0].kill()

