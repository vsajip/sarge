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

.. function:: run(command, input=None, async=False, **kwargs)

   This function is a convenience wrapper which constructs a
   :class:`Pipeline` instance from the passed parameters, and then invokes
   :meth:`~Pipeline.run` and :meth:`~Pipeline.close` on that instance.

   :param command: The command(s) to run.
   :type command: str
   :param input: Input data to be passed to the command(s). If text is passed,
                 it's converted to ``bytes`` using the default encoding. The
                 bytes are converted to a file-like object (a
                 :class:`BytesIO` instance).
   :type input: Text, bytes or a file-like object containing bytes (not text).
   :param kwargs: Any keyword parameters which you might want to pass to the
                   wrapped :class:`Pipeline` instance.
   :return: The created :class:`Pipeline` instance.

.. function:: capture_stdout(command, input=None, async=False, **kwargs)

   This function is a convenience wrapper which does the same as :func:`run`
   while capturing the ``stdout`` of the subprocess(es). This captured output
   is available through the ``stdout`` attribute of the return value from
   this function.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: As for :func:`run`.

.. function:: capture_stderr(command, input=None, async=False, **kwargs)

   This function is a convenience wrapper which does the same as :func:`run`
   while capturing the ``stderr`` of the subprocess(es). This captured output
   is available through the ``stderr`` attribute of the return value from
   this function.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: As for :func:`run`.

.. function:: capture_both(command, input=None, async=False, **kwargs)

   This function is a convenience wrapper which does the same as :func:`run`
   while capturing the ``stdout`` and the ``stderr`` of the subprocess(es).
   This captured output is available through the ``stdout`` and
   ``stderr`` attributes of the return value from this function.

   :param command: As for :func:`run`.
   :param input: As for :func:`run`.
   :param kwargs: As for :func:`run`.
   :return: As for :func:`run`.


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


   .. method:: run(input=None, async=False)

      Run the command.

      :param input: Input data to be passed to the command. If text is
                    passed, it's converted to ``bytes`` using the default
                    encoding. The bytes are converted to a file-like object (a
                    :class:`BytesIO` instance). The contents of the
                    file-like object are written to the ``stdin``
                    stream of the sub-process.
      :type input:  Text, bytes or a file-like object containing bytes.
      :param async: If ``True``, the command is run asynchronously - that is
                    to say, :meth:`wait` is not called on the underlying
                    :class:`~subprocess.Popen` instance.
      :type async: bool

   .. method:: wait()

     Wait for the command's underlying sub-process to complete.


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

   .. method:: run(input=None, async=False)

      Run the pipeline.

      :param input: The same as for the :meth:`Command.run` method.
      :param async: The same as for the :meth:`Command.run` method. Note that
                    parts of the pipeline may specify synchronous or
                    asynchronous running - this flag refers to the pipeline
                    as a whole.

   .. method:: wait()

      Wait for all command sub-processes to finish.

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

.. class:: Popen

   This is a subclass of :class:`subprocess.Popen` which is provided mainly
   to allow a process' ``stdout`` to be mapped to its ``stderr``. The
   standard library version allows you to specify ``stderr=STDOUT`` to
   indicate that the standard error stream of the sub-process be the same as
   its standard output stream. However. there's no facility in the standard
   library to do ``stdout=STDERR`` - but it *is* provided in this subclass.

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
pipeline - a set of commands connected such that the output streams of one
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
