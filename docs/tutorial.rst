.. _tutorial:

Tutorial
========

This is the place to start your practical exploration of ``sarge``.

Installation and testing
------------------------

sarge is a pure-Python library. You should be able to install it (when 
available on PyPI, **which is not yet**) using::

    pip install sarge

for installing ``sarge`` into a virtualenv or other directory where you have
write permissions. On Posix platforms, you may need to invoke using ``sudo``
if you need to install ``sarge`` in a protected location such as your system
Python's ``site-packages`` directory.

A full test suite is included with ``sarge``. To run it, you'll need to unpack
a source tarball and run ``python setup.py test`` in the top-level directory
of the unpack location. You can of course also run ``python setup.py install``
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
about what this is for now - it's more useful when more complex combinations of
commands are run.

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
available from ``sarge``, in one place - the :class:`Pipeline` instance that's
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
    "'ab?'"

This function is used internally by :func:`shell_format`, so you shouldn't need
to call it directly except in unusual cases.

Passing input to commands
-------------------------

You can pass input to a command pipeline using the ``input`` keyword parameter
to :func:`run`::

    >>> from sarge import run
    >>> p = run('cat|cat', input='foo')
    foo>>>

You can pass a string, bytes or a file-like object of bytes. If it's not
already, what you pass in is converted to a file-like object of bytes,
which is sent to the child process' ``stdin`` stream in a separate thread.

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
just decodes the former using the default encoding.

There are some convenience functions -- :func:`capture_stdout`,
:func:`capture_stderr` and :func:`capture_both` -- which work just like
:func:`run` but capture the relevant streams to :class:`Capture` instances,
which can be accessed using the appropriate attribute on the
:class:`Pipeline` instance returned from the functions.

Under the hood, a :class:`Capture` instance can capture output from one or
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
    >>> p = Command('/.receiver', stdout=Capture(buffer_size=1))
    >>> p.run(input=PIPE, async=True)
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

The ``p.returncode`` didn't print anything, indicating that the return code
was ``None``. This means that although the child process has exited,
it's still a zombie because we haven't "reaped" it by making a call to
:meth:`~Command.wait`. Once that's done, the zombie disappears and we get the
return code.

Note that two elements are needed for this example to work:

* We specify ``buffer_size=1`` in the Capture constructor. Without this,
  data would only be read into the Capture's queue after an I/O completes --
  which would depend on how many bytes the Capture reads at a time.
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

Environments
------------

In the :class:`subprocess.Popen` constructor, the ``env`` keyword argument, if
supplied, is expected to be the *complete* environment passed to the child
process. This can lead to problems on Windows, where if you don't pass the
``SYSTEMROOT`` environment variable, things can break. With ``sarge``, it's
assumed that anything you pass in ``env`` is *added* to the contents of
``os.environ``. This is almost always what you want - after all,
in a Posix shell, the environment is generally inherited with certain
additions for a specific command invocation.

Unicode and bytes
-----------------

All data between your process and sub-processes is communicated as bytes. Any
text passed as input to :func:`run` or a :meth:`~Pipeline.run` method will be
converted to bytes using the default encoding (usually UTF-8).

As ``sarge`` requires Python 2.6 or later, you can use ``from __future__
import unicode_literals`` and byte literals like ``b'foo'`` so that your code
looks and behaves the same under Python 2.x and Python 3.x.

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
pass ``async=True`` to run, in which case the call returns a :class:`Pipeline`
instance before all the commands in it have run. You will need to call
:meth:`~Pipeline.wait` or :meth:`~Pipeline.close` on this instance when you
are ready to synchronise with it; this is needed so that the sub processes
can be properly disposed of (otherwise, you will leave zombie processes
hanging around, which show up, for example, as ``<defunct>`` on Linux systems
when you run ``ps -ef``). Here's an example::

    >>> p = run('echo foo|cat|cat|cat|cat', async=True)
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

Next steps
----------

You might find it helpful to look at information about how ``sarge`` works
internally -- :ref:`internals` -- or the :ref:`reference`.
