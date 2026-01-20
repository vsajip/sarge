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
involved use of pipes, which also works identically on POSIX and Windows::

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
creation and communication on POSIX and Windows platforms, and presents the
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
   >>> p = run(cmd, stdout=Capture(), async_=True) # returns immediately
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

Sarge is intended to be used on and is tested on Python versions 2.7, 3.6 - 3.10, pypy
and pypy3 on Linux, Windows, and macOS.


Project status
--------------

The project has reached production/stable status in its development: there is a test
suite and it has been exercised on Windows, Ubuntu and Mac OS X. However,
because of the timing sensitivity of the functionality, testing needs to be
performed on as wide a range of hardware and platforms as possible.

The source repository for the project is on GitHub:

https://github.com/vsajip/sarge/

You can leave feedback by raising a new issue on the `issue
tracker <https://github.com/vsajip/sarge/issues/new/choose>`_.

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

.. _changelog:

Change log
----------

0.1.9 (future)
~~~~~~~~~~~~~~

Released: Not yet.


0.1.8
~~~~~

Released: 2026-01-20


- Fixed #55: Polled subcommands in order to return up-to-date return codes in
  ``Pipeline.returncodes``.

- Fixed #56: Ensure process_ready event is set at the appropriate time.

- Fixed #57: Stored exception in command node for use when in asynchronous mode.

- Fixed #58: Ensure ``Capture`` object has a ``flush`` method.


0.1.7
~~~~~

Released: 2021-12-10

- Fixed #50: Initialized `commands` attribute in a constructor.

- Fixed #52: Updated documentation to show improved command line parsing under Windows.

- Fixed #53: Added waiter.py to the manifest so that the test suite can be run.

0.1.6
~~~~~

Released: 2020-08-24

- Fixed #44: Added an optional timeout to :meth:`Command.wait` and
  :meth:`Pipeline.wait`, which only takes effect on Python >= 3.3.

- Fixed #47: Added the ``replace_env`` keyword argument which allows a complete
  replacement for ``os.environ`` to be passed.

- Fixed #51: Improved error handling around a ``Popen`` call.

0.1.5
~~~~~

Released: 2018-06-18

- Fixed #37: Instead of an OSError with a "no such file or directory" message,
  a ValueError is raised with a more informative "Command not found" message.

- Fixed #38: Replaced ``async`` keyword argument with ``async_``, as ``async``
  has become a keyword in Python 3.7.

- Fixed #39: Updated tutorial example on progress monitoring.

0.1.4
~~~~~

Released: 2015-01-24

- Fixed issue #21: Don't parse if shell=True.

- Fixed issue #20: Run pipeline in separate thread if async.

- Fixed issue #23: Return the correct return code when shell=True.

- Improved logging.

- Minor documentation updates.

- Minor additions to tests.

0.1.3
~~~~~

Released: 2014-01-17

- Fixed issue #15: Handled subprocess internal changes in Python 2.7.6.

- Improved logging support.

- Minor documentation updates.

0.1.2
~~~~~

Released: 2013-12-17

- Fixed issue #13: Removed module globals to improve thread safety.

- Fixed issue #12: Fixed a hang which occurred when a redirection failed.

- Fixed issue #11: Added ``+`` to the characters allowed in parameters.

- Fixed issue #10: Removed a spurious debugger breakpoint.

- Fixed issue #9: Relative pathnames in redirections are now relative to the
  current working directory for the redirected process.

- Added the ability to pass objects with ``fileno()`` methods as values
  to the ``input`` argument of ``run()``, and a ``Feeder`` class which
  facilitates passing data to child processes dynamically over time (rather
  than just an initial string, byte-string or file).

- Added functionality under Windows to use PATH, PATHEXT and the
  registry to find appropriate commands. This can e.g. convert a
  command ``'foo bar'``, if ``'foo.py'`` is a Python script in the
  ``c:\Tools`` directory which is on the path,  to the equivalent
  ``'c:\Python26\Python.exe c:\Tools\foo.py bar'``. This is done internally
  when a command is parsed, before it is passed to ``subprocess``.

- Fixed issue #7: Corrected handling of whitespace and redirections.

- Fixed issue #8: Added a missing import.

- Added Travis integration.

- Added encoding parameter to the ``Capture`` initializer.

- Fixed issue #6: addressed bugs in Capture logic so that iterating over
  captures is closer to ``subprocess`` behaviour.

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
