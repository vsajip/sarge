.. _reference:

API Reference
=============

This is the place where the functions and classes in ``sarge's`` public API
are described.

Attributes
----------

.. attribute:: default_capture_timeout

   This is the default timeout which will be used by :class:`Capture`
   instances when you don't specify one in the :class:`Capture` constructor.
   This is currently set to **0.02 seconds**.

Functions
---------

.. function:: run(command, input=None, async_=False, **kwargs)

   This function is a convenience wrapper which constructs a
   :class:`Pipeline` instance from the passed parameters, and then invokes
   :meth:`~Pipeline.run` and :meth:`~Pipeline.close` on that instance.

   :param command: The command(s) to run.
   :type command: str
   :param input: Input data to be passed to the command(s). If text is passed,
                 it's converted to ``bytes`` using the default encoding. The
                 bytes are converted to a file-like object (a
                 :class:`BytesIO` instance). If a value such as a file-like
                 object, integer file descriptor or special value like
                 ``subprocess.PIPE`` is passed, it is passed through
                 unchanged to :class:`subprocess.Popen`.
   :type input: Text, bytes or a file-like object containing bytes (not text).
   :param kwargs: Any keyword parameters which you might want to pass to the
                  wrapped :class:`Pipeline` instance. Apart from the ``input``
                  and ``async_`` keyword arguments described above, other
                  keyword arguments are passed to the wrapped
                  :class:`Pipeline` instance, and thence to
                  :class:`subprocess.Popen` via a :class:`Command` instance.
                  Note that the ``env`` kwarg is treated differently to how it
                  is in :class:`~subprocess.Popen`: it is treated as a set of
                  *additional* environment variables to be added to the values
                  in ``os.environ``, unless ``replace_env`` is also specified
                  as true, in which case the value of ``env`` becomes the
                  entire child process environment.

   :return: The created :class:`Pipeline` instance.

   .. versionchanged:: 0.1.5
      The ``async`` keyword parameter was changed to ``async_``, as ``async``
      is a keyword in Python 3.7 and later.

.. function:: capture_stdout(command, input=None, async_=False, **kwargs)

   This function is a convenience wrapper which does the same as :func:`run`
   while capturing the ``stdout`` of the subprocess(es). This captured output
   is available through the ``stdout`` attribute of the return value from
   this function.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: As for :func:`run`.

   .. versionchanged:: 0.1.5
      The ``async`` keyword parameter was changed to ``async_``, as ``async``
      is a keyword in Python 3.7 and later.

.. function:: get_stdout(command, input=None, async_=False, **kwargs)

   This function is a convenience wrapper which does the same as
   :func:`capture_stdout` but also returns the text captured. Use this when
   you know the output is not voluminous, so it doesn't matter that it's
   buffered in memory.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: The captured text.

   .. versionadded:: 0.1.1

   .. versionchanged:: 0.1.5
      The ``async`` keyword parameter was changed to ``async_``, as ``async``
      is a keyword in Python 3.7 and later.

.. function:: capture_stderr(command, input=None, async_=False, **kwargs)

   This function is a convenience wrapper which does the same as :func:`run`
   while capturing the ``stderr`` of the subprocess(es). This captured output
   is available through the ``stderr`` attribute of the return value from
   this function.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: As for :func:`run`.

   .. versionchanged:: 0.1.5
      The ``async`` keyword parameter was changed to ``async_``, as ``async``
      is a keyword in Python 3.7 and later.

.. function:: get_stderr(command, input=None, async_=False, **kwargs)

   This function is a convenience wrapper which does the same as
   :func:`capture_stderr` but also returns the text captured. Use this when
   you know the output is not voluminous, so it doesn't matter that it's
   buffered in memory.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: The captured text.

   .. versionadded:: 0.1.1

   .. versionchanged:: 0.1.5
      The ``async`` keyword parameter was changed to ``async_``, as ``async``
      is a keyword in Python 3.7 and later.

.. function:: capture_both(command, input=None, async_=False, **kwargs)

   This function is a convenience wrapper which does the same as :func:`run`
   while capturing the ``stdout`` and the ``stderr`` of the subprocess(es).
   This captured output is available through the ``stdout`` and
   ``stderr`` attributes of the return value from this function.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: As for :func:`run`.

   .. versionchanged:: 0.1.5
      The ``async`` keyword parameter was changed to ``async_``, as ``async``
      is a keyword in Python 3.7 and later.

.. function:: get_both(command, input=None, async_=False, **kwargs)

   This function is a convenience wrapper which does the same as
   :func:`capture_both` but also returns the text captured. Use this when
   you know the output is not voluminous, so it doesn't matter that it's
   buffered in memory.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: The captured text as a 2-element tuple, with the ``stdout`` text
            in the first element and the ``stderr`` text in the second.

   .. versionadded:: 0.1.1


   .. versionchanged:: 0.1.5
      The ``async`` keyword parameter was changed to ``async_``, as ``async``
      is a keyword in Python 3.7 and later.

.. function:: shell_quote(s)

   Quote text so that it is safe for Posix command shells.

   For example, "*.py" would be converted to "'*.py'". If the text is
   considered safe it is returned unquoted.

   :param s: The value to quote
   :type s: str, or unicode on 2.x
   :return: A safe version of the input, from the point of view of Posix
            command shells
   :rtype: The passed-in type

.. function:: shell_format(fmt, *args, **kwargs)

   Format a shell command with format placeholders and variables to fill
   those placeholders.

   Note: you must specify positional parameters explicitly, i.e. as {0}, {1}
   instead of {}, {}. Requiring the formatter to maintain its own counter can
   lead to thread safety issues unless a thread local is used to maintain
   the counter. It's not that hard to specify the values explicitly
   yourself :-)

   :param fmt: The shell command as a format string. Note that you will need
               to double up braces you want in the result, i.e. { -> {{ and
               } -> }}, due to the way :meth:`str.format` works.
   :type fmt: str, or unicode on 2.x
   :param args: Positional arguments for use with ``fmt``.
   :param kwargs: Keyword arguments for use with ``fmt``.
   :return: The formatted shell command, which should be safe for use in
            shells from the point of view of shell injection.
   :rtype: The type of ``fmt``.

Classes
-------

.. class:: Command(args, **kwargs)

   This represents a single command to be spawned as a subprocess.

   :param args: The command to run.
   :type args: str if ``shell=True``, or an array of str
   :param kwargs: Any keyword parameters you might pass to
                  :class:`~subprocess.Popen`, other than ``stdin`` (for which,
                  you need to see the ``input`` argument of
                  :meth:`~Command.run`).


   .. method:: run(input=None, async_=False)

      Run the command.

      :param input: Input data to be passed to the command. If text is
                    passed, it's converted to ``bytes`` using the default
                    encoding. The bytes are converted to a file-like object (a
                    :class:`BytesIO` instance). The contents of the
                    file-like object are written to the ``stdin``
                    stream of the sub-process.
      :type input:  Text, bytes or a file-like object containing bytes.
      :param async_: If ``True``, the command is run asynchronously -- that is
                    to say, :meth:`wait` is not called on the underlying
                    :class:`~subprocess.Popen` instance.
      :type async_: bool

      .. versionchanged:: 0.1.5
         The ``async`` keyword parameter was changed to ``async_``, as ``async``
         is a keyword in Python 3.7 and later.

   .. method:: wait(timeout=None)

      Wait for the command's underlying sub-process to complete, with a specified
      timeout. If the timeout is reached, a ``subprocess.TimeoutExpired`` exception
      is raised. The timeout is ignored in versions of Python < 3.3.

      .. versionchanged:: 0.1.6
         The ``timeout`` parameter was added.

   .. method:: terminate()

      Terminate the command's underlying sub-process by calling
      :meth:`subprocess.Popen.terminate` on it.

      .. versionadded:: 0.1.1

   .. method:: kill()

      Kill the command's underlying sub-process by calling
      :meth:`subprocess.Popen.kill` on it.

      .. versionadded:: 0.1.1

   .. method:: poll()

      Poll the command's underlying sub-process by calling
      :meth:`subprocess.Popen.poll` on it. Returns the result of that call.

      .. versionadded:: 0.1.1


.. class:: Pipeline(source, posix=True, **kwargs)

   This represents a set of commands which need to be run as a unit.

   :param source: The source text with the command(s) to run.
   :type source: str
   :param posix: Whether the source will be parsed using Posix conventions.
   :type posix: bool
   :param kwargs: Any keyword parameters you would pass to
                  :class:`subprocess.Popen`, other than ``stdin`` (for which,
                  you need to use the ``input`` parameter of the
                  :meth:`~Pipeline.run` method instead). You can pass
                  :class:`Capture` instances for ``stdout`` and ``stderr``
                  keyword arguments, which will cause those streams to be
                  captured to those instances.

   .. method:: run(input=None, async_=False)

      Run the pipeline.

      :param input: The same as for the :meth:`Command.run` method.
      :param async_: The same as for the :meth:`Command.run` method. Note that
                    parts of the pipeline may specify synchronous or
                    asynchronous running -- this flag refers to the pipeline
                    as a whole.

      .. versionchanged:: 0.1.5
         The ``async`` keyword parameter was changed to ``async_``, as ``async``
         is a keyword in Python 3.7 and later.

   .. method:: wait(timeout=None)

      Wait for all command sub-processes to finish, with an optional timeout. If the
      timeout is reached, a ``subprocess.TimeoutExpired`` exception is raised. The
      timeout is ignored in versions of Python < 3.3. If applied, it is applied to each
      of the pipeline's commands in turn, which means that the effective timeout might
      be cumulative.

      .. versionchanged:: 0.1.6
         The ``timeout`` parameter was added.

   .. method:: close()

      Wait for all command sub-processes to finish, and close all opened
      streams.

   .. attribute:: returncodes

      A list of the return codes of all sub-processes which were actually run.

   .. attribute:: returncode

      The return code of the last sub-process which was actually run.

   .. attribute:: commands

      The :class:`Command` instances which were actually created.


.. class:: Capture(timeout=None, buffer_size=0)

   A class which allows an output stream from a sub-process to be captured.

   :param timeout: The default timeout, in seconds. Note that you can
                   override this in particular calls to read input. If
                   ``None`` is specified, the value of the module attribute
                   ``default_capture_timeout`` is used instead.
   :type timeout: float
   :param buffer_size: The buffer size to use when reading from the underlying
                       streams. If not specified or specified as zero, a 4K
                       buffer is used. For interactive applications, use a value
                       of 1.
   :type buffer_size: int

   .. method:: read(size=-1, block=True, timeout=None)

     Like the ``read`` method of any file-like object.

     :param size: The number of bytes to read. If not specified, the intent is
                  to read the stream until it is exhausted.
     :type size: int
     :param block: Whether to block waiting for input to be available,
     :type block: bool
     :param timeout: How long to wait for input. If ``None``,
                     use the default timeout that this instance was
                     initialised with. If the result is ``None``, wait
                     indefinitely.
     :type timeout:  float

   .. method:: readline(size=-1, block=True, timeout=None)

     Like the ``readline`` method of any file-like object.

     :param size: As for the :meth:`~Capture.read` method.
     :param block: As for the :meth:`~Capture.read` method.
     :param timeout: As for the :meth:`~Capture.read` method.

   .. method:: readlines(sizehint=-1, block=True, timeout=None)

     Like the ``readlines`` method of any file-like object.

     :param sizehint: As for the :meth:`~Capture.read` method's ``size``.
     :param block: As for the :meth:`~Capture.read` method.
     :param timeout: As for the :meth:`~Capture.read` method.

   .. method:: expect(string_or_pattern,  timeout=None)

      This looks for a pattern in the captured output stream. If found, it
      returns immediately; otherwise, it will block until the timeout expires,
      waiting for a match as bytes from the captured stream continue to be read.

      :param string_or_pattern: A string or pattern representing a regular
                                expression to match. Note that this needs to
                                be a bytestring pattern if you pass a pattern
                                in; if you pass in text, it is converted to
                                bytes using the ``utf-8`` codec and then to
                                a pattern used for matching (using ``search``).
                                If you pass in a pattern, you may want to
                                ensure that its flags include ``re/MULTILINE``
                                so that you can make use of ``^`` and ``$`` in
                                matching line boundaries. Note that on Windows,
                                you may need to use ``\r?$`` to match ends of
                                lines, as ``$`` matches Unix newlines (LF) and
                                not Windows newlines (CRLF).

      :param timeout: If not specified, the module's ``default_expect_timeout``
                      is used.
      :returns: A regular expression match instance, if a match was found
                within the specified timeout, or ``None`` if no match was
                found.

   .. method:: close(stop_threads=False):

      Close the capture object. By default, this waits for the threads which
      read the captured streams to terminate (which may not happen unless the
      child process is killed, and the streams read to exhaustion). To ensure
      that the threads are stopped immediately, specify ``True`` for the
      ``stop_threads`` parameter, which will asks the threads to terminate
      immediately. This may lead to losing data from the captured streams
      which has not yet been read.


.. class:: Popen

   This is a subclass of :class:`subprocess.Popen` which is provided mainly
   to allow a process' ``stdout`` to be mapped to its ``stderr``. The
   standard library version allows you to specify ``stderr=STDOUT`` to
   indicate that the standard error stream of the sub-process be the same as
   its standard output stream. However. there's no facility in the standard
   library to do ``stdout=STDERR`` -- but it *is* provided in this subclass.

   In fact, the two streams can be swapped by doing ``stdout=STDERR,
   stderr=STDOUT`` in a call. The ``STDERR`` value is defined in ``sarge``
   as an integer constant which is understood by ``sarge`` (much as
   ``STDOUT`` is an integer constant which is understood by ``subprocess``).

Shell syntax understood by ``sarge``
------------------------------------

Shell commands are parsed by ``sarge`` using a simple parser.

Command syntax
^^^^^^^^^^^^^^

The ``sarge`` parser looks for commands which are separated by ``;`` and ``&``::

    echo foo; echo bar & echo baz

which means to run `echo foo`, wait for its completion,
and then run ``echo bar`` and then ``echo baz`` without waiting for ``echo
bar`` to complete.

The commands which are separated by ``&`` and ``;`` are *conditional* commands,
of the form::

    a && b

or::

    c || d

Here, command ``b`` is executed only if ``a`` returns success (i.e. a
return code of 0), whereas ``d`` is only executed if ``c`` returns failure,
i.e. a return code other than 0. Of course, in practice all of ``a``, ``b``,
``c`` and ``d`` could have arguments, not shown above for simplicity's sake.

Each operand on either side of ``&&`` or ``||`` could also consist of a
pipeline -- a set of commands connected such that the output streams of one
feed into the input stream of another. For example::

    echo foo | cat

or::

    command-a |& command-b

where the use of ``|`` indicates that the standard output of ``echo foo`` is
piped to the input of ``cat``, whereas the standard error of ``command-a`` is
piped to the input of ``command-b``.

Redirections
^^^^^^^^^^^^

The ``sarge`` parser also understands redirections such as are shown in the
following examples::

    command arg-1 arg-2 > stdout.txt
    command arg-1 arg-2 2> stderr.txt
    command arg-1 arg-2 2>&1
    command arg-1 arg-2 >&2

In general, file descriptors other than 1 and 2 are not allowed,
as the functionality needed to provided them (``dup2``) is not properly
supported on Windows. However, an esoteric special case *is* recognised::

    echo foo | tee stdout.log 3>&1 1>&2 2>&3 | tee stderr.log > /dev/null

This redirection construct will put ``foo`` in both ``stdout.log`` *and*
``stderr.log``. The effect of this construct is to swap the standard output
and standard error streams, using file descriptor 3 as a temporary as in the
code analogue for swapping variables ``a`` and ``b`` using temporary variable
``c``::

    c = a
    a = b
    b = c

This is recognised by ``sarge`` and used to swap the two streams,
though it doesn't literally use file descriptor ``3``,
instead using a cross-platform mechanism to fulfill the requirement.

You can see `this post <http://goo.gl/Enl0c>`_ for a longer explanation of
this somewhat esoteric usage of redirection.

Next steps
----------

You might find it helpful to look at the
`mailing list <http://groups.google.com/group/python-sarge/>`_.
