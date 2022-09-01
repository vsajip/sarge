.. _tutorial:

Tutorial
========

This is the place to start your practical exploration of ``sarge``.

Installation and testing
------------------------

sarge is a pure-Python library. You should be able to install it using::

    pip install sarge

for installing ``sarge`` into a virtualenv or other directory where you have
write permissions. On Posix platforms, you may need to invoke using ``sudo``
if you need to install ``sarge`` in a protected location such as your system
Python's ``site-packages`` directory.

A full test suite is included with ``sarge``. To run it, you'll need to unpack
a source tarball and run ``python setup.py test`` in the top-level directory
of the unpack location. You can of course also run ``pip install <archive>``
to install from the source tarball (perhaps invoking with ``sudo`` if you need
to install to a protected location).

Common usage patterns
---------------------

In the simplest cases, sarge doesn't provide any major advantage over
``subprocess``::

    >>> from sarge import run
    >>> run('echo "Hello, world!"')
    Hello, world!
    <sarge.Pipeline object at 0x1057110>

The ``echo`` command got run, as expected, and printed its output on the
console. In addition, a ``Pipeline`` object got returned. Don't worry too much
about what this is for now -- it's more useful when more complex combinations
of commands are run.

By comparison, the analogous case with ``subprocess`` would be::

    >>> from subprocess import call
    >>> call('echo "Hello, world!"'.split())
    "Hello, world!"
    0

We had to call :meth:`split` on the command (or we could have passed
``shell=True``), and as well as running the command, the :meth:`call` method
returned the exit code of the subprocess. To get the same effect with ``sarge``
you have to do::

    >>> from sarge import run
    >>> run('echo "Hello, world!"').returncode
    Hello, world!
    0

If that's as simple as you want to get, then of course you don't need
``sarge``. Let's look at more demanding uses next.

Finding commands under Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In versions 0.1.1 and earlier, ``sarge``, like ``subprocess``, did not do
anything special to find the actual executable to run -- it was expected to be
found in the current directory or the path. Specifically, ``PATHEXT`` was not
supported: where you might type ``yada`` in a command shell and have it run
``python yada.py`` because ``.py`` is in the ``PATHEXT`` environment variable
and Python is registered to handle files with that extension, neither
``subprocess`` (with ``shell=False``) nor ``sarge`` did this. You needed to
specify the executable name explicitly in the command passed to ``sarge``.

In 0.1.2 and later versions, ``sarge`` has improved command-line handling. The
"which" functionality has been backported from Python 3.3, which takes care of
using ``PATHEXT`` to resolve a command ``yada`` as ``c:\Tools\yada.py`` where
``c:\Tools`` is on the PATH and ``yada.py`` is in there. In addition, ``sarge``
queries the registry to see which programs are associated with the extension,
and updates the command line accordingly. Thus, a command line ``foo bar``
passed to ``sarge`` may actually result in ``c:\Windows\py.exe c:\Tools\foo.py
bar`` being passed to ``subprocess`` (assuming the Python Launcher for Windows,
``py.exe``, is associated with ``.py`` files).

This new functionality is not limited to Python scripts - it should
work for any extensions which are in ``PATHEXT`` and have an ftype/assoc
binding them to an executable through ``shell``, ``open`` and ``command``
subkeys in the registry, and where the command line is of the form
``"<path_to_executable>" "%1" %*`` (this is the standard form used by several
languages).

Parsing commands under Windows
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes, you may find it useful to pass ``posix=True`` for parsing command lines
under Windows (this is the default on POSIX platforms, so it doesn't need to be passed
explicitly there). Note the differences::

    >>> from sarge import parse_command_line
    >>> parse_command_line('git rev-list origin/master --since="1 hours ago"')
    CommandNode(command=['git', 'rev-list', 'origin/master', '--since="1', 'hours', 'ago"'] redirects={})
    >>> parse_command_line('git rev-list origin/master --since="1 hours ago"', posix=True)
    CommandNode(command=['git', 'rev-list', 'origin/master', '--since=1 hours ago'] redirects={})
    >>>

As you can see, passing ``posix=True`` has allowed the ``--since`` parameter to be
correctly handled.

Chaining commands
^^^^^^^^^^^^^^^^^

It's easy to chain commands together with ``sarge``. For example::

    >>> run('echo "Hello,"; echo "world!"')
    Hello,
    world!
    <sarge.Pipeline object at 0x247ed50>

whereas this would have been more involved if you were just using
``subprocess``::

    >>> call('echo "Hello,"'.split()); call('echo "world!"'.split())
    "Hello,"
    0
    "world!"
    0

You get two return codes, one for each command. The same information is
available from ``sarge``, in one place -- the :class:`Pipeline` instance that's
returned from a :func:`run` call::

    >>> run('echo "Hello,"; echo "world!"').returncodes
    Hello,
    world!
    [0, 0]

The :attr:`returncodes` property of a :class:`Pipeline` instance returns a
list of the return codes of all the commands that were run,
whereas the :attr:`returncode` property just returns the last element of
this list. The :class:`Pipeline` class defines a number of useful properties
- see the reference for full details.

Handling user input safely
^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, ``sarge`` does not run commands via the shell. This means that
wildcard characters in user input do not have potentially dangerous
consequences::

    >>> run('ls *.py')
    ls: cannot access *.py: No such file or directory
    <sarge.Pipeline object at 0x20f3dd0>

This behaviour helps to avoid `shell injection
<http://en.wikipedia.org/wiki/Code_injection#Shell_injection>`_ attacks.

There might be circumstances where you need to use ``shell=True``,
in which case you should consider formatting your commands with placeholders
and quoting any variable parts that you get from external sources (such as
user input). Which brings us on to ...

Formatting commands with placeholders for safe usage
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you need to merge commands with external inputs (e.g. user inputs) and you
want to prevent shell injection attacks, you can use the :func:`shell_format`
function. This takes a format string, positional and keyword arguments and
uses the new formatting (:meth:`str.format`) to produce the result::

    >>> from sarge import shell_format
    >>> shell_format('ls {0}', '*.py')
    "ls '*.py'"

Note how the potentially unsafe input has been quoted. With a safe input,
no quoting is done::

    >>> shell_format('ls {0}', 'test.py')
    'ls test.py'

If you really want to prevent quoting, even for potentially unsafe inputs,
just use the ``s`` conversion::

    >>> shell_format('ls {0!s}', '*.py')
    'ls *.py'

There is also a :func:`shell_quote` function which quotes potentially unsafe
input::

    >>> from sarge import shell_quote
    >>> shell_quote('abc')
    'abc'
    >>> shell_quote('ab?')
    "'ab?'"
    >>> shell_quote('"ab?"')
    '\'"ab?"\''
    >>> shell_quote("'ab?'")
    '"\'ab?\'"'

This function is used internally by :func:`shell_format`, so you shouldn't need
to call it directly except in unusual cases.

Passing input data to commands
------------------------------

You can pass input to a command pipeline using the ``input`` keyword parameter
to :func:`run`::

    >>> from sarge import run
    >>> p = run('cat|cat', input='foo')
    foo>>>

Here's how the value passed as ``input`` is processed:

* Text is encoded to bytes using UTF-8, which is then wrapped in a ``BytesIO``
  object.
* Bytes are wrapped in a ``BytesIO`` object.
* Starting with 0.1.2, if you pass an object with a ``fileno`` attribute,
  that will be called as a method and the resulting value will be  passed to
  the ``subprocess`` layer. This would normally be a readable file descriptor.
* Other values (such as integers representing OS-level file descriptors, or
  special values like ``subprocess.PIPE``) are passed to the ``subprocess``
  layer as-is.

If the result of the above process is a ``BytesIO`` instance (or if you passed
in a ``BytesIO`` instance), then ``sarge`` will spin up an internal thread to
write the data to the child process when it is spawned. The reason for a
separate thread is that if the child process consumes data slowly, or the size
of data is large, then the calling thread would block for potentially long
periods of time.

Passing input data to commands dynamically
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes, you may want to pass quite a lot of data to a child process which
is not conveniently available as a string, byte-string or a file, but which
is generated in the parent process (the one using ``sarge``) by some other
means. Starting with 0.1.2, ``sarge`` facilitates this by supporting objects
with ``fileno()`` attributes as described above, and includes a ``Feeder``
class which has a suitable ``fileno()`` implementation.

Creating and using a feeder is simple::

    import sys
    from sarge import Feeder, run

    feeder = Feeder()
    run([sys.executable, 'echoer.py'], input=feeder, async_=True)

After this, you can feed data to the child process' ``stdin`` by calling the
``feed()`` method of the ``Feeder`` instance::

    feeder.feed('Hello')
    feeder.feed(b'Goodbye')

If you pass in text, it will be encoded to bytes using UTF-8.

Once you've finished with the feeder, you can close it::

    feeder.close()

Depending on how quickly the child process consumes data, the thread calling
``feed()`` might block on I/O. If this is a problem, you can spawn a separate
thread which does the feeding.

Here's a complete working example::

    import os
    import subprocess
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

In the above example, the ``echoer.py`` script (included in the ``sarge``
source distribution, as it's part of the test suite) just reads lines from its
``stdin``, duplicates and prints to its ``stdout``. Since we passed in the
strings ``hello`` and ``goodbye``, the output from the script should be::

    hello hello
    goodbye goodbye


Chaining commands conditionally
-------------------------------

You can use ``&&`` and ``||`` to chain commands conditionally using
short-circuit Boolean semantics. For example::

    >>> from sarge import run
    >>> run('false && echo foo')
    <sarge.Pipeline object at 0xb8dd50>

Here, ``echo foo`` wasn't called, because the ``false`` command evaluates to
``False`` in the shell sense (by returning an exit code other than zero).
Conversely::

    >>> run('false || echo foo')
    foo
    <sarge.Pipeline object at 0xa11d50>

Here, ``foo`` is output because we used the ``||`` condition; because the left-
hand operand evaluates to ``False``, the right-hand operand is evaluated (i.e.
run, in this context). Similarly, using the ``true`` command::

    >>> run('true && echo foo')
    foo
    <sarge.Pipeline object at 0xb8dd50>
    >>> run('true || echo foo')
    <sarge.Pipeline object at 0xa11d50>


Creating command pipelines
--------------------------

It's just as easy to construct command pipelines::

    >>> run('echo foo | cat')
    foo
    <sarge.Pipeline object at 0xb8dd50>
    >>> run('echo foo; echo bar | cat')
    foo
    bar
    <sarge.Pipeline object at 0xa96c50>

Using redirection
-----------------

You can also use redirection to files as you might expect. For example::

    >>> run('echo foo | cat > /tmp/junk')
    <sarge.Pipeline object at 0x24b3190>
    ^D (to exit Python)
    $ cat /tmp/junk
    foo

You can use ``>``, ``>>``, ``2>``, ``2>>`` which all work as on Posix systems.
However, you can't use ``<`` or ``<<``.

To send things to the bit-bucket in a cross-platform way,
you can do something like::

    >>> run('echo foo | cat > %s' % os.devnull)
    <sarge.Pipeline object at 0x2765b10>

Capturing ``stdout`` and ``stderr`` from commands
-------------------------------------------------

To capture output for commands, just pass a :class:`Capture` instance for the
relevant stream::

    >>> from sarge import run, Capture
    >>> p = run('echo foo; echo bar | cat', stdout=Capture())
    >>> p.stdout.text
    u'foo\nbar\n'


The :class:`Capture` instance acts like a stream you can read from: it has
:meth:`~Capture.read`, :meth:`~Capture.readline` and :meth:`~Capture.readlines`
methods which you can call just like on any file-like object,
except that they offer additional options through ``block`` and ``timeout``
keyword parameters.

As in the above example, you can use the ``bytes`` or ``text`` property of a
:class:`Capture` instance to read all the bytes or text captured. The latter
just decodes the former using UTF-8 (the default encoding isn't used,
because on Python 2.x, the default encoding isn't UTF-8 -- it's ASCII).

There are some convenience functions -- :func:`capture_stdout`,
:func:`capture_stderr` and :func:`capture_both` -- which work just like
:func:`run` but capture the relevant streams to :class:`Capture` instances,
which can be accessed using the appropriate attribute on the
:class:`Pipeline` instance returned from the functions.

There are more convenience functions, :func:`get_stdout`, :func:`get_stderr`
and :func:`get_both`, which work just like :func:`capture_stdout`,
:func:`capture_stderr` and :func:`capture_both` respectively, but return the
captured text. For example::

    >>> from sarge import get_stdout
    >>> get_stdout('echo foo; echo bar')
    u'foo\nbar\n'

.. versionadded:: 0.1.1
   The :func:`get_stdout`, :func:`get_stderr` and :func:`get_both` functions
   were added.


A :class:`Capture` instance can capture output from one or
more sub-process streams, and will create a thread for each such stream so
that it can read all sub-process output without causing the sub-processes to
block on their output I/O. However, if you use a :class:`Capture`,
you should be prepared either to consume what it's read from the
sub-processes, or else be prepared for it all to be buffered in memory (which
may be problematic if the sub-processes generate a *lot* of output).

Iterating over captures
-----------------------

You can iterate over :class:`Capture` instances. By default you will get
successive lines from the captured data, as bytes; if you want text,
you can wrap with :class:`io.TextIOWrapper`. Here's an example using Python
3.2::

    >>> from sarge import capture_stdout
    >>> p = capture_stdout('echo foo; echo bar')
    >>> for line in p.stdout: print(repr(line))
    ...
    b'foo\n'
    b'bar\n'
    >>> p = capture_stdout('echo bar; echo baz')
    >>> from io import TextIOWrapper
    >>> for line in TextIOWrapper(p.stdout): print(repr(line))
    ...
    'bar\n'
    'baz\n'

This works the same way in Python 2.x. Using Python 2.7::

    >>> from sarge import capture_stdout
    >>> p = capture_stdout('echo foo; echo bar')
    >>> for line in p.stdout: print(repr(line))
    ...
    'foo\n'
    'bar\n'
    >>> p = capture_stdout('echo bar; echo baz')
    >>> from io import TextIOWrapper
    >>> for line in TextIOWrapper(p.stdout): print(repr(line))
    ...
    u'bar\n'
    u'baz\n'


Interacting with child processes
--------------------------------

Sometimes you need to interact with a child process in an interactive manner.
To illustrate how to do this, consider the following simple program,
named ``receiver``, which will be used as the child process::

    #!/usr/bin/env python
    import sys

    def main(args=None):
        while True:
            user_input = sys.stdin.readline().strip()
            if not user_input:
                break
            s = 'Hi, %s!\n' % user_input
            sys.stdout.write(s)
            sys.stdout.flush() # need this when run as a subprocess

    if __name__ == '__main__':
        sys.exit(main())

This just reads lines from the input and echoes them back as a greeting. If
we run it interactively::

    $ ./receiver
    Fred
    Hi, Fred!
    Jim
    Hi, Jim!
    Sheila
    Hi, Sheila!

The program exits on seeing an empty line.

We can now show how to interact with this program from a parent process::

    >>> from sarge import Command, Capture
    >>> from subprocess import PIPE
    >>> p = Command('./receiver', stdout=Capture(buffer_size=1))
    >>> p.run(input=PIPE, async_=True)
    Command('./receiver')
    >>> p.stdin.write('Fred\n')
    >>> p.stdout.readline()
    'Hi, Fred!\n'
    >>> p.stdin.write('Jim\n')
    >>> p.stdout.readline()
    'Hi, Jim!\n'
    >>> p.stdin.write('Sheila\n')
    >>> p.stdout.readline()
    'Hi, Sheila!\n'
    >>> p.stdin.write('\n')
    >>> p.stdout.readline()
    ''
    >>> p.returncode
    >>> p.wait()
    0

Note that the above code is for Python 2.x. If you're using Python 3.x, you need
to do some things slightly differently:

* Pass byte-strings to the streams, because interprocess communication occurs
  in bytes rather than text. In other words, use for example
  ``p.stdin.write(b'Fred\n')`` to send bytes to the child (otherwise you will
  get a ``TypeError``). Note that you'll also get byte-strings back.
* Add explicit ``p.stdin.flush()`` calls following ``p.stdin.write()`` calls, to
  ensure that the child process sees your output. You should do this even if
  you are running Python unbuffered (``-u``) in both parent and child processes
  (see https://github.com/vsajip/sarge/issues/43 and
  https://bugs.python.org/issue21332 for more information).

The ``p.returncode`` didn't print anything, indicating that the return code
was ``None``. This means that although the child process has exited,
it's still a zombie because we haven't "reaped" it by making a call to
:meth:`~Command.wait`. Once that's done, the zombie disappears and we get the
return code.

Buffering issues
^^^^^^^^^^^^^^^^

From the point of view of buffering, note that two elements are needed for
the above example to work:

* We specify ``buffer_size=1`` in the Capture constructor. Without this,
  data would only be read into the Capture's queue after an I/O completes --
  which would depend on how many bytes the Capture reads at a time. You can
  also pass a ``buffer_size=-1`` to indicate that you want to use line-
  buffering, i.e. read a line at a time from the child process. (This may only
  work as expected if the child process flushes its outbut buffers after every
  line.)
* We make a ``flush`` call in the ``receiver`` script, to ensure that the pipe
  is flushed to the capture queue. You could avoid the  ``flush`` call in the
  above example if you used ``python -u receiver`` as the command (which runs
  the script unbuffered).

This example illustrates that in order for this sort of interaction to work,
you need cooperation from the child process. If the child process has large
output buffers and doesn't flush them, you could be kept waiting for input
until the buffers fill up or a flush occurs.

If a third party package you're trying to interact with gives you buffering
problems, you may or may not have luck (on Posix, at least) using the
``unbuffer`` utility from the ``expect-dev`` package (do a Web search to find
it). This invokes a program directing its output to a pseudo-tty device which
gives line buffering behaviour. This doesn't always work, though :-(

Looking for specific patterns in child process output
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can look for specific patterns in the output of a child process, by using
the :meth:`~Capture.expect` method of the :class:`Capture` class. This takes a
string, bytestring or regular expression pattern object and a timeout, and
either returns a regular expression match object (if a match was found in the
specified timeout) or ``None`` (if no match was found in the specified
timeout). If you pass in a bytestring, it will be converted to a regular
expression pattern. If you pass in text, it will be encoded to bytes using the
``utf-8`` codec and then to a regular expression pattern. This pattern will be
used to look for a match (using ``search``). If you pass in a regular
expression pattern, make sure it is meant for bytes rather than text (to avoid
``TypeError`` on Python 3.x). You may also find it useful to specify
``re.MULTILINE`` in the pattern flags, so that you can match using ``^`` and
``$`` at line boundaries. Note that on Windows, you may need to use ``\r?$``
to match ends of lines, as ``$`` matches Unix newlines (LF) and not Windows
newlines (CRLF).

.. versionadded:: 0.1.1
   The ``expect`` method was added.

To illustrate usage of :meth:`Capture.expect`, consider the program
``lister.py`` (which is provided as part of the source distribution, as it's
used in the tests). This prints ``line 1``, ``line 2`` etc. indefinitely with
a configurable delay, flushing its output stream after each line. We can
capture the output from a run of ``lister.py``, ensuring that we use
line-buffering in the parent process::

    >>> from sarge import Capture, run
    >>> c = Capture(buffer_size=-1)     # line-buffering
    >>> p = run('python lister.py -d 0.01', async_=True, stdout=c)
    >>> m = c.expect('^line 1$')
    >>> m.span()
    (0, 6)
    >>> m = c.expect('^line 5$')
    >>> m.span()
    (28, 34)
    >>> m = c.expect('^line 1.*$')
    >>> m.span()
    (63, 70)
    >>> c.close(True)           # close immediately, discard any unread input
    >>> p.commands[0].kill()    # kill the subprocess
    >>> c.bytes[63:70]
    'line 10'
    >>> m = c.expect(r'^line 1\d\d$')
    >>> m.span()
    (783, 791)
    >>> c.bytes[783:791]
    'line 100'


Displaying progress as a child process runs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can display progress as a child process runs, assuming that its output
allows you to track that progress. Consider the following script,
``test_progress.py`` (which is included in the source distribution)::

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

When this is run without the ``--no-dots`` argument, you should see the
following::

    $ python progress.py
    ....................................................... (100 dots printed)
    Done - 100 lines seen.

If run *with* the ``--no-dots`` argument, you should see::

    $ python progress.py --no-dots
    Getting going ...
    Well on the way ...
    Almost there ...
    Done - 100 lines seen.

with short pauses between the output lines.


Direct terminal usage
^^^^^^^^^^^^^^^^^^^^^

Some programs don't work through their ``stdin``/``stdout``/``stderr``
streams, instead opting to work directly with their controlling terminal. In
such cases, you can't work with these programs using ``sarge``; you need to use
a pseudo-terminal approach, such as is provided by (for example)
`pexpect <http://noah.org/wiki/pexpect>`_. ``Sarge`` works within the limits
of the :mod:`subprocess` module, which means sticking to ``stdin``, ``stdout``
and ``stderr`` as ordinary streams or pipes (but not pseudo-terminals).

Examples of programs which work directly through their controlling terminal
are ``ftp`` and ``ssh`` - the password prompts for these programs are
generally always printed to the controlling terminal rather than ``stdout`` or
``stderr``.

.. _environments:

Environments
------------

In the :class:`subprocess.Popen` constructor, the ``env`` keyword argument, if
supplied, is expected to be the *complete* environment passed to the child
process. This can lead to problems on Windows, where if you don't pass the
``SYSTEMROOT`` environment variable, things can break. With ``sarge``, it's
assumed by default that anything you pass in ``env`` is *added* to the
contents of ``os.environ``. This is almost always what you want -- after all,
in a Posix shell, the environment is generally inherited with certain
additions for a specific command invocation. However, if you want to pass a
complete environment rather than an augmented ``os.environ``, you can do this
by passing ``replace_env=True`` in the keyword arguments. In that case, the
value of the ``env`` keyword argument is passed as-is to the child process.

.. versionadded:: 0.1.6
   The ``replace_env`` keyword parameter was added.

.. note:: On Python 2.x on Windows, environment keys and values must be of
   type ``str`` - Unicode values will cause a ``TypeError``. Be careful of
   this if you use ``from __future__ import unicode_literals``. For example,
   the test harness for sarge uses Unicode literals on 2.x,
   necessitating the use of different logic for 2.x and 3.x::

        if PY3:
            env = {'FOO': 'BAR'}
        else:
            # Python 2.x wants native strings, at least on Windows
            env = { b'FOO': b'BAR' }


Working directory and other options
-----------------------------------

You can set the working directory for a :class:`Command` or :class:`Pipeline`
using the ``cwd`` keyword argument to the constructor, which is passed through
to the subprocess when it's created. Likewise, you can use the other keyword
arguments which are accepted by the :class:`subprocess.Popen` constructor.

Avoid using the ``stdin`` keyword argument -- instead, use the ``input`` keyword
argument to the :meth:`Command.run` and :meth:`Pipeline.run` methods, or the
:func:`run`, :func:`capture_stdout`, :func:`capture_stderr`, and
:func:`capture_both` functions. The ``input`` keyword makes it easier for you
to pass literal text or byte data.

Unicode and bytes
-----------------

All data between your process and sub-processes is communicated as bytes. Any
text passed as input to :func:`run` or a :meth:`~Pipeline.run` method will be
converted to bytes using UTF-8 (the default encoding isn't used, because on
Python 2.x, the default encoding isn't UTF-8 -- it's ASCII).

As ``sarge`` requires Python 2.6 or later, you can use ``from __future__
import unicode_literals`` and byte literals like ``b'foo'`` so that your code
looks and behaves the same under Python 2.x and Python 3.x. (See the note on
using native string keys and values in :ref:`environments`.)

As mentioned above, :class:`Capture` instances return bytes, but you can wrap
with :class:`io.TextIOWrapper` if you want text.


Use as context managers
-----------------------

The :class:`Capture` and :class:`Pipeline` classes can be used as context
managers::

    >>> with Capture() as out:
    ...     with Pipeline('cat; echo bar | cat', stdout=out) as p:
    ...         p.run(input='foo\n')
    ...
    <sarge.Pipeline object at 0x7f3320e94310>
    >>> out.read().split()
    ['foo', 'bar']


Synchronous and asynchronous execution of commands
--------------------------------------------------

By default. commands passed to :func:`run` run synchronously,
i.e. all commands run to completion before the call returns. However, you can
pass ``async_=True`` to run, in which case the call returns a :class:`Pipeline`
instance before all the commands in it have run. You will need to call
:meth:`~Pipeline.wait` or :meth:`~Pipeline.close` on this instance when you
are ready to synchronise with it; this is needed so that the sub processes
can be properly disposed of (otherwise, you will leave zombie processes
hanging around, which show up, for example, as ``<defunct>`` on Linux systems
when you run ``ps -ef``). Here's an example::

    >>> p = run('echo foo|cat|cat|cat|cat', async_=True)
    >>> foo

Here, ``foo`` is printed to the terminal by the last ``cat`` command, but all
the sub-processes are zombies. (The ``run`` function returned immediately,
so the interpreter got to issue the ``>>>` prompt *before* the ``foo`` output
was printed.)

In another terminal, you can see the zombies::

    $ ps -ef | grep defunct | grep -v grep
    vinay     4219  4217  0 19:27 pts/0    00:00:00 [echo] <defunct>
    vinay     4220  4217  0 19:27 pts/0    00:00:00 [cat] <defunct>
    vinay     4221  4217  0 19:27 pts/0    00:00:00 [cat] <defunct>
    vinay     4222  4217  0 19:27 pts/0    00:00:00 [cat] <defunct>
    vinay     4223  4217  0 19:27 pts/0    00:00:00 [cat] <defunct>

Now back in the interactive Python session, we call :meth:`~Pipeline.close` on
the pipeline::

    >>> p.close()

and now, in the other terminal, look for defunct processes again::

    $ ps -ef | grep defunct | grep -v grep
    $

No zombies found :-)

Handling errors in asynchronous mode
------------------------------------

If an exception occurs calling :meth:`~Command.run` when trying to start a child
process in synchronous mode, it's raised immediately. However, when running in
asynchronous mode (`async_=True`), there will be a command pipeline which is run in a
separate thread. In this case, the exception is caught in that thread but not
propagated to the calling thread; instead, it is stored in the `exception` attribute of
the :class:`Command` instance. The `process` attribute of that instance will be `None`,
as the child process couldn't be started.

You can check the `exception` attributes of commands in a :class:`Pipeline` instance to
see if any have occurred.

.. versionadded:: 0.18
   The `exception` attribute was added to :class:`Command`.

About threading and forking on Posix
------------------------------------

If you run commands asynchronously by using ``&`` in a command pipeline, then a
thread is spawned to run each such command asynchronously. Remember that thread
scheduling behaviour can be unexpected -- things may not always run in the order
you expect. For example, the command line::

    echo foo & echo bar & echo baz

should run all of the ``echo`` commands concurrently as far as possible,
but you can't be sure of the exact sequence in which these commands complete --
it may vary from machine to machine and even from one run to the next. This has
nothing to do with ``sarge`` -- there are no guarantees with just plain Bash,
either.

On Posix, :mod:`subprocess` uses :func:`os.fork` to create the child process,
and you may see dire warnings on the Internet about mixing threads, processes
and ``fork()``. It *is* a heady mix, to be sure: you need to understand what's
going on in order to avoid nasty surprises. If you run into any such, it may be
hard to get help because others can't reproduce the problems. However, that's
no reason to shy away from providing the functionality altogether. Such issues
do not occur on Windows, for example: because Windows doesn't have a
``fork()`` system call, child processes are created in a different way which
doesn't give rise to the issues which sometimes crop up in a Posix environment.

For an exposition of the sort of things which might bite you if you are using locks,
threading and ``fork()`` on Posix, see `this post
<https://web.archive.org/web/20211015140727/http://www.linuxprogrammingblog.com/threads-and-fork-think-twice-before-using-them>`_.

Other resources on this topic:

* http://bugs.python.org/issue6721

Please report any problems you find in this area (or any other) either via the
`mailing list <http://groups.google.com/group/python-sarge/>`_ or the `issue
tracker <https://github.com/vsajip/sarge/issues/new/choose>`_.

Next steps
----------

You might find it helpful to look at information about how ``sarge`` works
internally -- :ref:`internals` -- or peruse the :ref:`reference`.
