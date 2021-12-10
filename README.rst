.. image:: https://travis-ci.org/vsajip/sarge.svg
   :target: https://travis-ci.org/vsajip/sarge

.. image:: https://coveralls.io/repos/vsajip/sarge/badge.svg
   :target: https://coveralls.io/github/vsajip/sarge

Overview
========
The sarge package provides a wrapper for subprocess which provides command
pipeline functionality.

This package leverages subprocess to provide easy-to-use cross-platform command
pipelines with a Posix flavour: you can have chains of commands using ``;``, ``&``,
pipes using ``|`` and ``|&``, and redirection.

Requirements & Installation
---------------------------
The sarge package requires Python 2.6 or greater, and can be
installed with the standard Python installation procedure::

    python setup.py install

There is a set of unit tests which you can invoke with::

    python setup.py test

before running the installation.

Availability & Documentation
----------------------------
The latest version of sarge can be found on `GitHub <https://github.com/vsajip/sarge/>`_.

The latest documentation (kept updated between releases) is on `Read The Docs <http://sarge.readthedocs.org/>`_:

Please report any problems or suggestions for improvement either via the
`mailing list <http://groups.google.com/group/python-sarge/>`_ or the `issue
tracker <https://github.com/vsajip/sarge/issues/new/choose>`_.

