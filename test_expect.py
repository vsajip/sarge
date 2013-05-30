import logging
from sarge import run, Capture
import time

logger = logging.getLogger(__name__)

logging.basicConfig(filename='test_expect.log', filemode='w',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(name)s %(threadName)s %(lineno)4d %(message)s')
cap = Capture(buffer_size=-1)   # line buffered
p = run('python slow_lister.py docs/_build/html/tutorial.html', async=True,
        stdout=cap)
stime = time.time()
logger.info('Calling expect for head')
cap.expect('<head>', 60.0)
logger.info('Returned from expect for head')
elapsed = time.time() - stime
if not cap.match:
    print('<head> not found within time limit.')
else:
    print('<head> found at %s in %.1f seconds.' % (cap.match.span(), elapsed))
    stime = time.time()
    logger.info('Calling expect for body')
    cap.expect('<body>', 60.0)
    logger.info('Returned from expect for body')
    elapsed = time.time() - stime
    if not cap.match:
        print('<body> not found within time limit.')
    else:
        print('<body> found at %s in %.1f seconds.' % (cap.match.span(), elapsed))
logger.debug('Killing subprocess')
p.commands[0].kill()
logger.debug('Closing capture')
cap.close()

