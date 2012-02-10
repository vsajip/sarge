# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Vinay M. Sajip. See LICENSE for licensing information.
#
# Test harness for sarge: Subprocess Allegedly Rewards Good Encapsulation :-)
#

from io import TextIOWrapper
import logging
import os
import shutil
import sys
import tempfile
import unittest

from sarge import (shell_quote, Capture, Command, CommandLineParser, Pipeline,
                   shell_format, run, parse_command_line, capture_stdout,
                   capture_stderr, capture_both, Popen)
from sarge.shlext import shell_shlex
from stack_tracer import start_trace, stop_trace

TRACE_THREADS = True    # debugging only

if os.name == 'nt': #pragma: no cover
    FILES = ('libiconv2.dll', 'libintl3.dll', 'cat.exe', 'echo.exe',
             'tee.exe', 'false.exe', 'true.exe', 'sleep.exe', 'touch.exe')
    for fn in FILES:
        if not os.path.exists(fn):
            list = '%s and %s' % (', '.join(FILES[:-1]), FILES[-1])
            raise ImportError('To run these tests on Windows, '
                              'you need the GnuWin32 coreutils package. This '
                              'appears not to be installed correctly, '
                              'as the file %r does not appear to be in the '
                              'current directory.\nSee http://gnuwin32'
                              '.sourceforge.net/packages/coreutils.htm for '
                              'download details. Once downloaded and '
                              'installed, you need to copy %s to '
                              'the test directory or have the directory they'
                              ' were installed to on the PATH.' % (fn, list))

logger = logging.getLogger(__name__)

EMITTER = '''#!/usr/bin/env python
import sys

sys.stdout.write('foo\\n')
sys.stderr.write('bar\\n')
'''

class SargeTest(unittest.TestCase):
    def tearDown(self):
        logger.debug('=' * 60)

    def test_quote(self):
        self.assertEqual(shell_quote(''), "''")
        self.assertEqual(shell_quote('a'), 'a')
        self.assertEqual(shell_quote('*'), "'*'")
        self.assertEqual(shell_quote('foo'), 'foo')
        self.assertEqual(shell_quote("'*.py'"), "'*.py'")
        self.assertEqual(shell_quote("*.py"), "'*.py'")
        self.assertEqual(shell_quote("'*.py"), "''\"'\"'*.py'")

    def test_formatter(self):
        self.assertEqual(shell_format('ls {0}', '*.py'), "ls '*.py'")
        self.assertEqual(shell_format('ls {0!s}', '*.py'), "ls *.py")

    def send_to_capture(self, c, s):
        rd, wr = os.pipe()
        c.add_stream(os.fdopen(rd, 'rb'))
        os.write(wr, s)
        os.close(wr)

    def test_capture(self):
        logger.debug('test_capture started')
        with Capture() as c:
            self.send_to_capture(c, b'foofoo')
            self.assertEqual(c.read(3), b'foo')
            self.assertEqual(c.read(3), b'foo')
            self.assertEqual(c.read(), b'')
        logger.debug('test_capture finished')

    def test_command_splitting(self):
        logger.debug('test_command started')
        cmd = 'echo foo'
        c = Command(cmd)
        self.assertEqual(c.args, cmd.split())
        c = Command(cmd, shell=True)
        self.assertEqual(c.args, cmd)

    def test_command_no_stdin(self):
        self.assertRaises(ValueError, Command, 'cat', stdin='xyz')

    def test_literal_input(self):
        with Capture() as out:
            self.assertEqual(run('cat', stdout=out, input='foo').returncode, 0)
            self.assertEqual(out.read(), b'foo')

    def test_read_extra(self):
        with Capture() as out:
            self.assertEqual(run('cat', stdout=out, input='bar').returncode, 0)
            self.assertEqual(out.read(5), b'bar')

    def test_shell_redirection(self):
        with Capture() as err:
            self.assertEqual(run('cat >&2', stderr=err, shell=True,
                                 input='bar').returncode, 0)
            self.assertEqual(err.read(), b'bar')

    def test_capture_bytes(self):
        with Capture() as err:
            self.assertEqual(run('cat >&2', stderr=err, shell=True,
                                 input='bar').returncode, 0)
        self.assertEqual(err.bytes, b'bar')
        with Capture() as err:
            self.assertEqual(run('cat >&2', stderr=err, shell=True,
                                 input='bar').returncode, 0)
        self.assertEqual(err.text, 'bar')

    def ensure_testfile(self):
        if not os.path.exists('testfile.txt'):  #pragma: no cover
            with open('testfile.txt', 'w') as f:
                for i in range(10000):
                    f.write('Line %d\n' % (i + 1))

    def test_run_sync(self):
        self.ensure_testfile()
        with open('testfile.txt') as f:
            content = f.readlines()
        with Capture() as out:
            self.assertEqual(
                run('cat testfile.txt testfile.txt', stdout=out).returncode, 0)
            lines = out.readlines()
            self.assertEqual(len(lines), len(content) * 2)

    def test_run_async(self):
        self.ensure_testfile()
        with open('testfile.txt', 'rb') as f:
            content = f.read().splitlines(True)
        with Capture() as out:
            p = run('cat testfile.txt testfile.txt', stdout=out,
                    async=True)
            # Do some other work in parallel, including reading from the
            # concurrently running child process
            out.readline()
            out.readline()
            # kill some time ...
            for i in range(10):
                with open('testfile.txt') as f:
                    f.read()
            p.wait()
            self.assertEqual(p.returncode, 0)
            lines = out.readlines()
            self.assertEqual(len(lines), len(content) * 2 - 2)

    def test_env(self):
        e = os.environ
        c = Command('echo foo', env={'FOO': 'BAR'})
        d = c.kwargs['env']
        ek = set(e)
        dk = set(d)
        ek.add('FOO')
        self.assertEqual(dk, ek)
        self.assertEqual(d['FOO'], 'BAR')

    def test_shlex(self):
        TESTS = (
            ('',
             []),
            ('a',
             [('a', 'a')]),
            ('a && b\n',
             [('a', 'a'), ('&&', 'c'), ('b', 'a')]),
            ('a | b; c>/fred/jim-sheila.txt|&d;e&',
             [('a', 'a'), ('|', 'c'), ('b', 'a'), (';', 'c'), ('c', 'a'),
                 ('>', 'c'), ('/fred/jim-sheila.txt', 'a'), ('|&', 'c'),
                 ('d', 'a'),
                 (';', 'c'), ('e', 'a'), ('&', 'c')])
        )
        for posix in False, True:
            for s, expected in TESTS:
                s = shell_shlex(s, posix=posix, control=True)
                actual = []
                while True:
                    t, tt = s.get_token(), s.token_type
                    if not t:
                        break
                    actual.append((t, tt))
                self.assertEqual(actual, expected)

    def test_shlex_without_control(self):
        TESTS = (
            ('',
             []),
            ('a',
             [('a', 'a')]),
            ('a && b\n',
             [('a', 'a'), ('&', 'a'), ('&', 'a'), ('b', 'a')]),
            ('a | b; c>/fred/jim-sheila.txt|&d;e&',
             [('a', 'a'), ('|', 'a'), ('b', 'a'), (';', 'a'), ('c', 'a'),
                 ('>', 'a'), ('/fred/jim-sheila.txt', 'a'), ('|', 'a'),
                 ('&', 'a'),
                 ('d', 'a'), (';', 'a'), ('e', 'a'), ('&', 'a')])
        )
        for posix in False, True:
            for s, expected in TESTS:
                s = shell_shlex(s, posix=posix)
                actual = []
                while True:
                    t, tt = s.get_token(), s.token_type
                    if not t:
                        break
                    actual.append((t, tt))
                self.assertEqual(actual, expected)

    def test_shlex_with_quoting(self):
        TESTS = (
            ('"a b"', False, [('"a b"', '"')]),
            ('"a b"', True, [('a b', 'a')]),
            ('"a b"  c# comment', False, [('"a b"', '"'), ('c', 'a')]),
            ('"a b"  c# comment', True, [('a b', 'a'), ('c', 'a')]),
        )
        for s, posix, expected in TESTS:
            s = shell_shlex(s, posix=posix)
            actual = []
            while True:
                t, tt = s.get_token(), s.token_type
                if not t:
                    break
                actual.append((t, tt))
            self.assertEqual(actual, expected)
        s = shell_shlex('"abc')
        self.assertRaises(ValueError, s.get_token)

    def test_parsing(self):
        parse_command_line('abc')
        parse_command_line('abc " " # comment')
        parse_command_line('abc \ "def"')
        parse_command_line('(abc)')
        self.assertRaises(ValueError, parse_command_line, '(abc')
        self.assertRaises(ValueError, parse_command_line, '&&')
        parse_command_line('(abc>def)')
        parse_command_line('(abc 2>&1; def >>&2)')
        parse_command_line('(a|b;c d && e || f >ghi jkl 2> mno)')
        parse_command_line('(abc; (def)); ghi & ((((jkl & mno)))); pqr')

    def test_parsing_special(self):
        for cmd in ('ls -l --color=auto', 'sleep 0.5', 'ls /tmp/abc.def',
                    'ls *.py?'):
            node = parse_command_line(cmd)
            self.assertEqual(node.command, cmd.split())

    def test_parsing_controls(self):
        clp = CommandLineParser()
        gvc = clp.get_valid_controls
        self.assertEqual(gvc('>>>>'), ['>>', '>>'])
        self.assertEqual(gvc('>>'), ['>>'])
        self.assertEqual(gvc('>>>'), ['>>', '>'])
        self.assertEqual(gvc('>>>>>'), ['>>', '>>', '>'])
        self.assertEqual(gvc('))))'), [')', ')', ')', ')'])
        self.assertEqual(gvc('>>;>>'), ['>>', ';', '>>'])
        self.assertEqual(gvc(';'), [';'])
        self.assertEqual(gvc(';;'), [';', ';'])
        self.assertEqual(gvc(');'), [')', ';'])
        self.assertEqual(gvc('>&'), ['>', '&'])
        self.assertEqual(gvc('>>&'), ['>>', '&'])
        self.assertEqual(gvc('||&'), ['||', '&'])
        self.assertEqual(gvc('|&'), ['|&'])

    #def test_scratch(self):
    #    import pdb; pdb.set_trace()
    #    parse_command_line('(a|b;c d && e || f >ghi jkl 2> mno)')

    def test_parsing_errors(self):
        self.assertRaises(ValueError, parse_command_line, '(abc')
        self.assertRaises(ValueError, parse_command_line, '(abc |&| def')
        self.assertRaises(ValueError, parse_command_line, '&&')
        self.assertRaises(ValueError, parse_command_line, 'abc>')
        self.assertRaises(ValueError, parse_command_line, 'a 3> b')
        self.assertRaises(ValueError, parse_command_line, 'abc >&x')
        self.assertRaises(ValueError, parse_command_line, 'a > b | c')
        self.assertRaises(ValueError, parse_command_line, 'a 2> b |& c')
        self.assertRaises(ValueError, parse_command_line, 'a > b > c')
        self.assertRaises(ValueError, parse_command_line, 'a > b >> c')
        self.assertRaises(ValueError, parse_command_line, 'a 2> b 2> c')
        self.assertRaises(ValueError, parse_command_line, 'a 2>> b 2>> c')
        self.assertRaises(ValueError, parse_command_line, 'a 3> b')

    def test_pipeline_no_input_stdout(self):
        with Capture() as out:
            with Pipeline('echo foo 2> %s | cat | cat' % os.devnull,
                          stdout=out) as pl:
                pl.run()
            self.assertEqual(out.read().strip(), b'foo')

    def test_pipeline_no_input_stderr(self):
        with Capture() as err:
            with Pipeline('echo foo 2> %s | cat | cat >&2' % os.devnull,
                          stderr=err) as pl:
                pl.run()
            self.assertEqual(err.read().strip(), b'foo')

    def test_pipeline_no_input_pipe_stderr(self):
        with Capture() as err:
            with Pipeline('echo foo 2> %s | cat >&2 |& cat >&2' %
                          os.devnull, stderr=err) as pl:
                pl.run()
            self.assertEqual(err.read().strip(), b'foo')

    def test_pipeline_with_input_stdout(self):
        logger.debug('starting')
        with Capture() as out:
            with Pipeline('cat 2>> %s | cat | cat' % os.devnull,
                          stdout=out) as pl:
                pl.run(input='foo' * 1000)
            self.assertEqual(out.read().strip(), b'foo' * 1000)

    def test_pipeline_no_input_redirect_stderr(self):
        with Capture() as err:
            with Pipeline('echo foo 2> %s | cat 2>&1 | cat >&2' % os.devnull,
                          stderr=err) as pl:
                pl.run()
            self.assertEqual(err.read().strip(), b'foo')

    def test_pipeline_swap_outputs(self):
        for fn in ('stdout.log', 'stderr.log'):
            if os.path.exists(fn):
                os.unlink(fn)
        with Pipeline('echo foo | tee stdout.log 3>&1 1>&2 2>&3 | '
                      'tee stderr.log > %s' % os.devnull) as pl:
            pl.run()
            with open('stdout.log') as f:
                self.assertEqual(f.read().strip(), 'foo')
            with open('stderr.log') as f:
                self.assertEqual(f.read().strip(), 'foo')
        for fn in ('stdout.log', 'stderr.log'):
            os.unlink(fn)

    def test_pipeline_large_file(self):
        if os.path.exists('dest.bin'):  #pragma: no cover
            os.unlink('dest.bin')
        if not os.path.exists('random.bin'):    #pragma: no cover
            with open('random.bin', 'wb') as f:
                f.write(os.urandom(20 * 1048576))
        with Pipeline('cat random.bin | cat | cat | cat | cat | '
                      'cat > dest.bin ') as pl:
            pl.run()
        with open('random.bin', 'rb') as f:
            data1 = f.read()
        with open('dest.bin', 'rb') as f:
            data2 = f.read()
        os.unlink('dest.bin')
        self.assertEqual(data1, data2)

    def test_logical_and(self):
        with Capture() as out:
            with Pipeline('false && echo foo', stdout=out) as pl:
                pl.run()
        self.assertEqual(out.read().strip(), b'')
        with Capture() as out:
            with Pipeline('true && echo foo', stdout=out) as pl:
                pl.run()
        self.assertEqual(out.read().strip(), b'foo')
        with Capture() as out:
            with Pipeline('false | cat && echo foo', stdout=out) as pl:
                pl.run()
        self.assertEqual(out.read().strip(), b'foo')

    def test_logical_or(self):
        with Capture() as out:
            with Pipeline('false || echo foo', stdout=out) as pl:
                pl.run()
        self.assertEqual(out.read().strip(), b'foo')
        with Capture() as out:
            with Pipeline('true || echo foo', stdout=out) as pl:
                pl.run()
        self.assertEqual(out.read().strip(), b'')

    def test_list(self):
        with Capture() as out:
            with Pipeline('echo foo > %s; echo bar' % os.devnull,
                          stdout=out) as pl:
                pl.run()
        self.assertEqual(out.read().strip(), b'bar')

    def test_list_merge(self):
        with Capture() as out:
            with Pipeline('echo foo; echo bar; echo baz', stdout=out) as pl:
                pl.run()
        self.assertEqual(out.read().split(), [b'foo', b'bar', b'baz'])

    def test_capture_when_other_piped(self):
        with Capture() as out:
            with Pipeline('echo foo; echo bar |& cat', stdout=out) as pl:
                pl.run()
        self.assertEqual(out.read().split(), [b'foo', b'bar'])

    def test_pipeline_func(self):
        self.assertEqual(run('false').returncode, 1)
        with Capture() as out:
            self.assertEqual(run('echo foo', stdout=out).returncode, 0)
        self.assertEqual(out.bytes.strip(), b'foo')

    def test_double_redirect(self):
        with Capture() as out:
            self.assertRaises(ValueError, run, 'echo foo > %s' % os.devnull,
                              stdout=out)
        with Capture() as out:
            with Capture() as err:
                self.assertRaises(ValueError, run,
                                  'echo foo 2> %s' % os.devnull, stdout=out,
                                  stderr=err)

    def test_pipeline_async(self):
        logger.debug('starting')
        with Capture() as out:
            p = run('echo foo & (sleep 2; echo bar) &  (sleep 1; echo baz)',
                    stdout=out)
            self.assertEqual(p.returncode, 0)
        items = out.bytes.split()
        for item in (b'foo', b'bar', b'baz'):
            self.assertTrue(item in items)
        self.assertTrue(items.index(b'bar') > items.index(b'baz'))

    def ensure_emitter(self):
        if not os.path.exists('emitter.py'): #pragma: no cover
            with open('emitter.py', 'w') as f:
                f.write(EMITTER)

    def test_capture_stdout(self):
        p = capture_stdout('echo foo')
        self.assertEqual(p.stdout.text.strip(), 'foo')

    def test_capture_stderr(self):
        self.ensure_emitter()
        p = capture_stderr('"%s" emitter.py > %s' % (sys.executable,
                                                     os.devnull))
        self.assertEqual(p.stderr.text.strip(), 'bar')

    def test_capture_both(self):
        self.ensure_emitter()
        p = capture_both('"%s" emitter.py' % sys.executable)
        self.assertEqual(p.stdout.text.strip(), 'foo')
        self.assertEqual(p.stderr.text.strip(), 'bar')

    def test_byte_iterator(self):
        p = capture_stdout('echo foo; echo bar')
        lines = []
        for line in p.stdout:
            lines.append(line.strip())
        self.assertEqual(lines, [b'foo', b'bar'])

    def test_text_iterator(self):
        p = capture_stdout('echo foo; echo bar')
        lines = []
        for line in TextIOWrapper(p.stdout):
            lines.append(line)
        self.assertEqual(lines, ['foo\n', 'bar\n'])

    def test_partial_line(self):
        p = capture_stdout('echo foobarbaz')
        lines = [p.stdout.readline(6), p.stdout.readline().strip()]
        self.assertEqual(lines, [b'foobar', b'baz'])

    def test_returncodes(self):
        p = capture_stdout('echo foo; echo bar; echo baz; false')
        self.assertEqual(p.returncodes, [0, 0, 0, 1])
        self.assertEqual(p.returncode, 1)

    def test_processes(self):
        p = capture_stdout('echo foo; echo bar; echo baz; false')
        plist = p.processes
        for p in plist:
            self.assertTrue(isinstance(p, Popen))

    def test_command_run(self):
        c = Command('echo foo'.split(), stdout=Capture())
        c.run()
        self.assertEqual(c.returncode, 0)

    def test_working_dir(self):
        d = tempfile.mkdtemp()
        try:
            run('touch newfile.txt', cwd=d)
            files = os.listdir(d)
            self.assertEqual(files, ['newfile.txt'])
        finally:
            shutil.rmtree(d)

if __name__ == '__main__':  #pragma: no cover
    # switch the level to DEBUG for in-depth logging.
    fn = 'test_sarge-%d.%d.log' % sys.version_info[:2]
    logging.basicConfig(level=logging.DEBUG, filename=fn, filemode='w',
                        format='%(threadName)s %(funcName)s %(lineno)d '
                               '%(message)s')
    logging.getLogger('sarge.parse').setLevel(logging.WARNING)
    fn = 'threads-%d.%d.log' % sys.version_info[:2]
    if TRACE_THREADS:
        start_trace(fn)
    try:
        unittest.main()
    finally:
        if TRACE_THREADS:
            stop_trace()
