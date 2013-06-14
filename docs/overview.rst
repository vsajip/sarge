Overview
========

Start here for all things ``sarge``.

What is Sarge for?
------------------

If you want to interact with external programs from your Python applications,
Sarge is a library which is intended to make your life easier than using the
:mod:`subprocess` module in Python's standard library.

Sarge is, of course, short for sergeant -- and like any good non-commissioned
officer, ``sarge`` works to issue commands on your behalf and to inform you
about the results of running those commands.

The acronym lovers among you might be amused to learn that sarge can also
stand for "Subprocess Allegedly Rewards Good Encapsulation" :-)

Here's a taster (example suggested by Kenneth Reitz's Envoy documentation)::

    >>> from sarge import capture_stdout
    >>> p = capture_stdout('fortune|cowthink')
    >>> p.returncode
    0
    >>> p.commands
    [Command('fortune'), Command('cowthink')]
    >>> p.returncodes
    [0, 0]
    >>> print(p.stdout.text)
     ____________________________________
    ( The last thing one knows in        )
    ( constructing a work is what to put )
    ( first.                             )
    (                                    )
    ( -- Blaise Pascal                   )
     ------------------------------------
            o   ^__^
             o  (oo)\_______
                (__)\       )\/\
                    ||----w |
                    ||     ||

The :func:`capture_stdout` function is a convenient form of an underlying
function, :func:`run`. You can also use conditionals::

    >>> from sarge import run
    >>> p = run('false && echo foo')
    >>> p.commands
    [Command('false')]
    >>> p.returncodes
    [1]
    >>> p.returncode
    1
    >>> p = run('false || echo foo')
    foo
    >>> p.commands
    [Command('false'), Command('echo foo')]
    >>> p.returncodes
    [1, 0]
    >>> p.returncode
    0

The conditional logic is being done by sarge and not the shell -- which means
you can use the identical code on Windows. Here's an example of some more
involved use of pipes, which also works identically on Posix and Windows::

    >>> cmd = 'echo foo | tee stdout.log 3>&1 1>&2 2>&3 | tee stderr.log > %s' % os.devnull
    >>> p = run(cmd)
    >>> p.commands
    [Command('echo foo'), Command('tee stdout.log'), Command('tee stderr.log')]
    >>> p.returncodes
    [0, 0, 0]
    >>>
    vinay@eta-oneiric64:~/projects/sarge$ cat stdout.log
    foo
    vinay@eta-oneiric64:~/projects/sarge$ cat stderr.log
    foo

In the above example, the first tee invocation swaps its ``stderr`` and
``stdout`` -- see `this post <http://goo.gl/Enl0c>`_ for a longer explanation
of this somewhat esoteric usage.

Why not just use ``subprocess``?
--------------------------------

The :mod:`subprocess` module in the standard library contains some very
powerful functionality. It encapsulates the nitty-gritty details of subprocess
creation and communication on Posix and Windows platforms, and presents the
application programmer with a uniform interface to the OS-level facilities.
However, :mod:`subprocess` does not do much more than this,
and is difficult to use in some scenarios. For example:

* You want to use command pipelines, but using ``subprocess`` out of the box
  often leads to deadlocks because pipe buffers get filled up.
* You want to use bash-style pipe syntax on Windows,
  but Windows shells don't support some of the syntax you want to use,
  like ``&&``, ``||``, ``|&`` and so on.
* You want to process output from commands in a flexible way,
  and :meth:`~subprocess.Popen.communicate` is not flexible enough for your
  needs -- for example, you need to process output a line at a time.
* You want to avoid `shell injection
  <http://en.wikipedia.org/wiki/Code_injection#Shell_injection>`_ problems by
  having the ability to quote your command arguments safely.
* :mod:`subprocess` allows you to let ``stderr`` be the same as ``stdout``,
  but not the other way around -- and you need to do that.

Main features
-------------

Sarge offers the following features:

* A simple run command which allows a rich subset of Bash-style shell
  command syntax, but parsed and run by sarge so that you can run on Windows
  without ``cygwin``.
* The ability to format shell commands with placeholders,
  such that variables are quoted to prevent shell injection attacks::

   >>> from sarge import shell_format
   >>> shell_format('ls {0}', '*.py')
   "ls '*.py'"
   >>> shell_format('cat {0}', 'a file name with spaces')
   "cat 'a file name with spaces'"

* The ability to capture output streams without requiring you to program your
  own threads. You just use a :class:`Capture` object and then you can read
  from it as and when you want::

   >>> from sarge import Capture, run
   >>> with Capture() as out:
   ...     run('echo foobarbaz', stdout=out)
   ...
   <sarge.Pipeline object at 0x175ed10>
   >>> out.read(3)
   'foo'
   >>> out.read(3)
   'bar'
   >>> out.read(3)
   'baz'
   >>> out.read(3)
   '\n'
   >>> out.read(3)
   ''

  A :class:`Capture` object can capture the output from multiple commands::

   >>> from sarge import run, Capture
   >>> p = run('echo foo; echo bar; echo baz', stdout=Capture())
   >>> p.stdout.readline()
   'foo\n'
   >>> p.stdout.readline()
   'bar\n'
   >>> p.stdout.readline()
   'baz\n'
   >>> p.stdout.readline()
   ''

  Delays in commands are honoured in asynchronous calls::

   >>> from sarge import run, Capture
   >>> cmd = 'echo foo & (sleep 2; echo bar) & (sleep 1; echo baz)'
   >>> p = run(cmd, stdout=Capture(), async=True) # returns immediately
   >>> p.close() # wait for completion
   >>> p.stdout.readline()
   'foo\n'
   >>> p.stdout.readline()
   'baz\n'
   >>> p.stdout.readline()
   'bar\n'
   >>>

Here, the ``sleep`` commands ensure that the asynchronous ``echo`` calls
occur in the order ``foo`` (no delay), ``baz`` (after a delay of one second)
and ``bar`` (after a delay of two seconds); the capturing works as expected.


Python version and platform compatibility
-----------------------------------------

Sarge is intended to be used on any Python version >= 2.6 and is tested on
Python versions 2.6, 2.7, 3.1, 3.2 and 3.3 on Linux, Windows, and Mac OS X (not
all versions are tested on all platforms, but are expected to work correctly).


Project status
--------------

The project has reached alpha status in its development: there is a test
suite and it has been exercised on Windows, Ubuntu and Mac OS X. However,
because of the timing sensitivity of the functionality, testing needs to be
performed on as wide a range of hardware and platforms as possible.

The source repository for the project is on BitBucket:

https://bitbucket.org/vinay.sajip/sarge/

You can leave feedback by raising a new issue on the `issue
tracker <https://bitbucket.org/vinay.sajip/sarge/issues/new>`_
(BitBucket registration not necessary, but recommended).

.. note:: For testing under Windows, you need to install the `GnuWin32
   coreutils <http://gnuwin32.sourceforge.net/packages/coreutils.htm>`_
   package, and copy the relevant executables (currently ``libiconv2.dll``,
   ``libintl3.dll``, ``cat.exe``, ``echo.exe``, ``tee.exe``, ``false.exe``,
   ``true.exe``, ``sleep.exe`` and ``touch.exe``) to the directory from which
   you run the test harness (``test_sarge.py``).


API stability
-------------

Although every attempt will be made to keep API changes to the absolute minimum,
it should be borne in mind that the software is in its very early stages. For
example, the asynchronous feature (where commands are run in separate threads
when you specify ``&`` in a command pipeline) can be considered experimental,
and there may be changes in this area. However, you aren't forced to use this
feature, and ``sarge`` should be useful without it.

Change log
----------

0.1.2
~~~~~

Released: Not yet.

- Added functionality under Windows to use PATH, PATHEXT and the
  registry to find appropriate commands. This can e.g. convert a
  command ``'foo bar'``, if ``'foo.py'`` is a Python script in the
  ``c:\Tools`` directory which is on the path,  to the equivalent
  ``'c:\Python26\Python.exe c:\Tools\foo.py bar'``.

- Fixed issue #7: Corrected handling of whitespace and redirections.

- Fixed issue #8: Added a missing import.

- Added Travis integration.

- Added encoding parameter to the ``Capture`` initializer.

- Fixed bugs in Capture logic so that iterating over captures is
  closer to ``subprocess`` behaviour.

- Tests added to cover added functionality and reported issues.

- Numerous documentation updates.


0.1.1
~~~~~

Released: 2013-06-04

- ``expect`` method added to ``Capture`` class, to allow searching
  for specific patterns in subprocess output streams.

- added ``terminate``, ``kill`` and ``poll`` methods to ``Command``
  class to operate on the wrapped subprocess.

- ``Command.run`` now propagates exceptions which occur while spawning
  subprocesses.

- Fixed issue #4: ``shell_shlex`` does not split on ``@``.

- Fixed issue #3: ``run`` et al now accept commands as lists, just as
  ``subprocess.Popen`` does.

- Fixed issue #2: ``shell_quote`` implementation improved.

- Improved ``shell_shlex`` resilience by handling Unicode on 2.x (where
  ``shlex`` breaks if passed Unicode).

- Added ``get_stdout``, ``get_stderr`` and ``get_both`` for when subprocess
  output is not expected to be voluminous.

- Added an internal lock to serialise access to shared data.

- Tests added to cover added functionality and reported issues.

- Numerous documentation updates.


0.1
~~~

Released: 2012-02-10

- Initial release.


Next steps
----------

You might find it helpful to look at the :ref:`tutorial`, or the
:ref:`reference`.
