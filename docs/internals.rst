.. _internals:

Under the hood
==============

This is the section where some description of how ``sarge`` works internally
will be provided, as and when time permits.

How capturing works
-------------------

This section describes how :class:`Capture` is implemented.

Basic approach
^^^^^^^^^^^^^^

A :class:`Capture` consists of a queue, some output streams from sub-processes,
and some threads to read from those streams into the queue. One thread is
created for each stream, and the thread exits when its stream has been
completely read. When you read from a :class:`Capture` instance using methods
like :meth:`~Capture.read`, :meth:`~Capture.readline` and
:meth:`~Capture.readlines`, you are effectively reading from the queue.

Blocking and timeouts
^^^^^^^^^^^^^^^^^^^^^

Each of the :meth:`~Capture.read`, :meth:`~Capture.readline` and
:meth:`~Capture.readlines` methods has optional ``block`` and ``timeout``
keyword arguments. These default to ``True`` and ``None`` respectively,
which means block indefinitely until there's some data - the standard
behaviour for file-like objects. However, these can be overridden internally
in a couple of ways:

* The :class:`Capture` constructor takes an optional ``timeout`` keyword
  argument. This defaults to ``None``, but if specified, that's the timeout used
  by the ``readXXX`` methods unless you specify values in the method calls.
  If ``None`` is specified in the constructor, the module attribute
  :attr:`default_capture_timeout` is used, which is currently set to 0.02
  seconds. If you need to change this default, you can do so before any
  :class:`Capture` instances are created (or just provide an alternative default
  in every :class:`Capture` creation).
* If all streams feeding into the capture have been completely read,
  then ``block`` is always set to ``False``.


Implications when handling large amounts of data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There shouldn't be any special implications of handling large amounts of
data, other than buffering, buffer sizes and memory usage (which you would
have to think about anyway). Here's an example of piping a 20MB file into  a
capture across several process boundaries::

    $ ls -l random.bin
    -rw-rw-r-- 1 vinay vinay 20971520 2012-01-17 17:57 random.bin
    $ python
    [snip]
    >>> from sarge import run, Capture
    >>> p = run('cat random.bin|cat|cat|cat|cat|cat', stdout=Capture(), async=True)
    >>> for i in range(8):
    ...     data = p.stdout.read(2621440)
    ...     print('Read chunk %d: %d bytes' % (i, len(data)))
    ...
    Read chunk 0: 2621440 bytes
    Read chunk 1: 2621440 bytes
    Read chunk 2: 2621440 bytes
    Read chunk 3: 2621440 bytes
    Read chunk 4: 2621440 bytes
    Read chunk 5: 2621440 bytes
    Read chunk 6: 2621440 bytes
    Read chunk 7: 2621440 bytes
    >>> p.stdout.read()
    ''


Swapping output streams
-----------------------

A new constant, ``STDERR``, is defined by ``sarge``. If you specify
``stdout=STDERR``, this means that you want the child process ``stdout`` to
be the same as its ``stderr``. This is analogous to the core functionality in
:class:`subprocess.Popen` where you can specify ``stderr=STDOUT`` to have the
child process ``stderr`` be the same as its ``stdout``. The use of this
constant also allows you to swap the child's ``stdout`` and ``stderr``,
which can be useful in some cases.

This functionality works through a class :class:`sarge.Popen` which subclasses
:class:`subprocess.Popen` and overrides the internal ``_get_handles`` method to
work the necessary magic - which is to duplicate, close and swap handles as
needed.

How shell quoting works
-----------------------

The :func:`shell_quote` function works as follows. Firstly,
an empty string is converted to ``''``. Next, a check is made to see if the
string has already been quoted (i.e. it begins and ends with the ``'``
character), and if so, it is returned unchanged. Otherwise,
it's bracketed with the ``'`` character and every internal instance of ``'``
is replaced with ``'"'"'``.

How shell command formatting works
----------------------------------

This is inspired by Nick Coghlan's `shell_command <https://bitbucket
.org/ncoghlan/shell_command>`_ project. An internal :class:`ShellFormatter`
class is derived from :class:`string.Formatter` and overrides the
:meth:`string.Formatter.convert_field` method to provide quoting for placeholder
values. This formatter is simpler than Nick's in that it forces you to
explicitly provide the indices of positional arguments: You have to use e.g.
``'cp {0} {1}`` instead of ``cp {} {}``. This avoids the need to keep an
internal counter in the formatter, which would make its implementation be not
thread-safe without additional work.

How command parsing works
-------------------------

Internally ``sarge`` uses a simple recursive descent parser to parse commands.
A simple BNF grammar for the parser would be::

    <list> ::= <pipeline> ((";" | "&") <pipeline>)*
    <pipeline> ::= <logical> (("&&" | "||") <logical>)*
    <logical> ::= (<command> (("|" | "|&") <command>)*) | "(" <list> ")"
    <command> ::= <command-part>+
    <command-part> ::= WORD ((<NUM>)? (">" | ">>") (<WORD> | ("&" <NUM>)))*

where WORD and NUM are terminal tokens with the meanings you would expect.

The parser constructs a parse tree, which is used internally by the
:class:`Pipeline` class to manage the running of the pipeline.

The standard library's :mod:`shlex` module contains a class which is used for
lexical scanning. Since the :class:`shlex.shlex` class is not able to provide
the needed functionality, ``sarge`` includes a module, ``shlext``,
which defines a subclass, ``shell_shlex``, which provides the necessary
functionality. This is not part of the public API of ``sarge``, though it has
been `submitted as an
enhancement <http://bugs.python.org/issue1521950#msg150761>`_ on the Python
issue tracker.

Thread debugging
----------------

Sometimes, you can get deadlocks even though you think you've taken
sufficient measures to avoid them. To help identify where deadlocks are
occurring, the ``sarge`` source distribution includes a module,
``stack_tracer``, which is based on MIT-licensed code by László Nagy in an
`ActiveState recipe <http://code.activestate.com/recipes/577334/>`_. To see how
it's invoked, you can look at the ``sarge`` test harness ``test_sarge.py`` --
this is set to invoke the tracer if the ``TRACE_THREADS`` variable is set (which
it is, by default). If the unit tests hang on your system, then the
``threads-X.Y.log`` file will show where the deadlock is (just look and see what
all the threads are waiting for).

Future changes
--------------

At the moment, if a :class:`Capture` is used, it will read from its sub-process
output streams into a queue, which can then be read by your code. If you don't
read from the :class:`Capture` in a timely fashion, a lot of data could
potentially be buffered in memory - the same thing that happens when you use
:meth:`subprocess.Popen.communicate`. There might be added some means of
"turning the tap off", i.e. pausing the reader threads so that the capturing
threads stop reading from the sub-process streams. This will, of course, cause
those sub-processes to block on their I/O, so at some point the tap would need
to be turned back on. However, such a facility would afford better
sub-process control in some scenarios.

Next steps
----------

You might find it helpful to look at the :ref:`reference`.
