# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2021 Vinay M. Sajip. See LICENSE for licensing information.
#
# Test harness for sarge: Subprocess Allegedly Rewards Good Encapsulation :-)
#

from __future__ import unicode_literals

from io import TextIOWrapper
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from sarge import (shell_quote, Capture, Command, CommandLineParser, Pipeline,
                   shell_format, run, parse_command_line, capture_stdout,
                   get_stdout, capture_stderr, get_stderr, capture_both,
                   get_both, Popen, Feeder)
from sarge.shlext import shell_shlex
from stack_tracer import start_trace, stop_trace

if sys.platform == 'win32':  #pragma: no cover
    from sarge.utils import find_command

TRACE_THREADS = sys.platform not in ('cli',)    # debugging only

PY3 = sys.version_info[0] >= 3

logger = logging.getLogger(__name__)

EMITTER = '''#!/usr/bin/env python
import sys

sys.stdout.write('foo\\n')
sys.stderr.write('bar\\n')
'''

SEP = '=' * 60

def missing_files():
    result = []  # on POSIX, nothing missing
    if os.name == 'nt':  #pragma: no cover

        def found_file(fn):
            if os.path.exists(fn):
                return True
            for d in os.environ['PATH'].split(os.pathsep):
                p = os.path.join(d, fn)
                if os.path.exists(p):
                    return True
            return False

        files = ('cat.exe', 'echo.exe', 'tee.exe', 'false.exe', 'true.exe',
                 'sleep.exe', 'touch.exe')

        # Looking for the DLLs used by the above - perhaps this check isn't
        # needed, as if the .exes were installed properly, we should be OK. The
        # DLL check is relevant for GnuWin32 but may not be for MSYS, MSYS2 etc.
        if not os.environ.get('USE_MSYS', ''):
            files = ('libiconv2.dll', 'libintl3.dll') + files

        path_dirs = os.environ['PATH'].split(os.pathsep)

        for fn in files:
            if os.path.exists(fn):
                found = True  # absolute, or in current directory
            else:
                found = False
                for d in path_dirs:
                    p = os.path.join(d, fn)
                    if os.path.exists(p):
                        found = True
                        break
            if not found:
                result.append(fn)

    return result

ERROR_MESSAGE = '''
Can't find one or more of the files needed for testing:

%s

You may need to install the GnuWin32 coreutils package, MSYS, or an equivalent.
'''.strip()

missing = missing_files()
if missing:
    missing = ', '.join(missing)
    print(ERROR_MESSAGE % missing)
    sys.exit(1)
del missing

class SargeTest(unittest.TestCase):
    def setUp(self):
        logger.debug(SEP)
        logger.debug(self.id().rsplit('.', 1)[-1])
        logger.debug(SEP)

    def test_quote(self):
        self.assertEqual(shell_quote(''), "''")
        self.assertEqual(shell_quote('a'), 'a')
        self.assertEqual(shell_quote('*'), "'*'")
        self.assertEqual(shell_quote('foo'), 'foo')
        self.assertEqual(shell_quote("'*.py'"), "''\\''*.py'\\'''")
        self.assertEqual(shell_quote("'a'; rm -f b; true 'c'"),
                                     "''\\''a'\\''; rm -f b; true '\\''c'\\'''")
        self.assertEqual(shell_quote("*.py"), "'*.py'")
        self.assertEqual(shell_quote("'*.py"), "''\\''*.py'")

    def test_quote_with_shell(self):
        from subprocess import PIPE, Popen

        if os.name != 'posix':  #pragma: no cover
            raise unittest.SkipTest('This test works only on POSIX')

        workdir = tempfile.mkdtemp()
        try:
            s = "'\\\"; touch %s/foo #'" % workdir
            cmd = 'echo %s' % shell_quote(s)
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            p.communicate()
            self.assertEqual(p.returncode, 0)
            files = os.listdir(workdir)
            self.assertEqual(files, [])
            fn = "'ab?'"
            cmd = 'touch %s/%s' % (workdir, shell_quote(fn))
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            p.communicate()
            self.assertEqual(p.returncode, 0)
            files = os.listdir(workdir)
            self.assertEqual(files, ["'ab?'"])
        finally:
            shutil.rmtree(workdir)

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
        # run with a list (see Issue #3)
        with Capture() as out:
            self.assertEqual(
                run(['cat', 'testfile.txt', 'testfile.txt'],
                    stdout=out).returncode, 0)
            lines = out.readlines()
            self.assertEqual(len(lines), len(content) * 2)

    def test_run_async(self):
        self.ensure_testfile()
        with open('testfile.txt', 'rb') as f:
            content = f.read().splitlines(True)
        with Capture(timeout=1) as out:
            p = run('cat testfile.txt testfile.txt', stdout=out,
                    async_=True)
            # Do some other work in parallel, including reading from the
            # concurrently running child process
            read_count = 0
            if out.readline():
                read_count += 1
            if out.readline():
                read_count += 1
            # kill some time ...
            for i in range(10):
                with open('testfile.txt') as f:
                    f.read()
            p.wait()
            self.assertEqual(p.returncode, 0)
            lines = out.readlines()
            self.assertEqual(len(lines), len(content) * 2 - read_count)

    def test_env(self):
        e = os.environ
        if PY3:
            env = {'FOO': 'BAR'}
        else:
            # Python 2.x wants native strings, at least on Windows
            # (and literals are Unicode in this module)
            env = { b'FOO': b'BAR' }
        c = Command('echo foo', env=env)
        d = c.kwargs['env']
        ek = set(e)
        dk = set(d)
        ek.add('FOO')
        self.assertEqual(dk, ek)
        self.assertEqual(d['FOO'], 'BAR')
        c = Command('echo foo', env=env, replace_env=True)
        ek = set(env)
        dk = set(c.kwargs['env'])
        self.assertEqual(dk, ek)
        self.assertEqual(dk, {'FOO'})

    def test_env_usage(self):
        if os.name == 'nt':
            cmd = 'echo %FOO%'
        else:
            cmd = 'echo $FOO'
        if PY3:
            env = {'FOO': 'BAR'}
        else:
            # Python 2.x wants native strings, at least on Windows
            # (and literals are Unicode in this module)
            env = { b'FOO': b'BAR' }
        c = Command(cmd, env=env, stdout=Capture(), shell=True)
        c.run()
        self.assertEqual(c.stdout.text.strip(), 'BAR')

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

    def test_shlex_with_misc_chars(self):
        TESTS = (
            ('rsync user.name@host.domain.tld:path dest',
             ('rsync', 'user.name@host.domain.tld:path', 'dest')),
            (r'c:\Python26\Python lister.py -d 0.01',
             (r'c:\Python26\Python', 'lister.py', '-d', '0.01')),
        )
        for s, t in TESTS:
            sh = shell_shlex(s)
            self.assertEqual(tuple(sh), t)

    def test_shlex_issue_31(self):
        cmd = "python -c 'print('\''ok'\'')'"
        list(shell_shlex(cmd, control='();>|&', posix=True))
        shell_format("python -c {0}", "print('ok')")
        list(shell_shlex(cmd, control='();>|&', posix=True))

    def test_shlex_issue_34(self):
        cmd = "ls foo,bar"
        actual = list(shell_shlex(cmd))
        self.assertEqual(actual, ['ls', 'foo,bar'])

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
        c = parse_command_line('git rev-list origin/master --since="1 hours ago"', posix=True)
        self.assertEqual(c.command, ['git', 'rev-list', 'origin/master',
                                     '--since=1 hours ago'])

    def test_parsing_special(self):
        for cmd in ('ls -l --color=auto', 'sleep 0.5', 'ls /tmp/abc.def',
                    'ls *.py?', r'c:\Python26\Python lister.py -d 0.01'):
            node = parse_command_line(cmd, posix=False)
            if sys.platform != 'win32':
                self.assertEqual(node.command, cmd.split())
            else:
                split = cmd.split()[1:]
                self.assertEqual(node.command[1:], split)

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
        if os.name != 'posix':
            raise unittest.SkipTest('This test works only on POSIX')
        with Capture() as err:
            with Pipeline('echo foo 2> %s | cat | cat >&2' % os.devnull,
                          stderr=err) as pl:
                pl.run()
            self.assertEqual(err.read().strip(), b'foo')

    def test_pipeline_no_input_pipe_stderr(self):
        if os.name != 'posix':
            raise unittest.SkipTest('This test works only on POSIX')
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
        if os.name != 'posix':
            raise unittest.SkipTest('This test works only on POSIX')
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
            p = run('echo foo & (sleep 2; echo bar) & (sleep 1; echo baz)',
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

    def test_get_stdout(self):
        s = get_stdout('echo foo; echo bar')
        self.assertEqual(s.split(), ['foo', 'bar'])

    def test_capture_stderr(self):
        self.ensure_emitter()
        p = capture_stderr('"%s" emitter.py > %s' % (sys.executable,
                                                     os.devnull))
        self.assertEqual(p.stderr.text.strip(), 'bar')

    def test_get_stderr(self):
        self.ensure_emitter()
        s = get_stderr('"%s" emitter.py > %s' % (sys.executable, os.devnull))
        self.assertEqual(s.strip(), 'bar')

    def test_get_both(self):
        self.ensure_emitter()
        t = get_both('"%s" emitter.py' % sys.executable)
        self.assertEqual([s.strip() for s in t], ['foo', 'bar'])

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

    def test_command_nonexistent(self):
        c = Command('nonesuch foo'.split(), stdout=Capture())
        if PY3:
            ARR = self.assertRaisesRegex
        else:
            ARR = self.assertRaisesRegexp
        ARR(ValueError, 'Command not found: nonesuch', c.run)

    def test_pipeline_nonexistent(self):
        p = Pipeline('nonesuch foo'.split(), stdout=Capture())
        self.assertEqual(p.commands, [])
        self.assertEqual(p.returncodes, [])
        self.assertEqual(p.processes, [])
        if PY3:
            ARR = self.assertRaisesRegex
        else:
            ARR = self.assertRaisesRegexp
        ARR(ValueError, 'Command not found: nonesuch', p.run)

    def test_working_dir(self):
        d = tempfile.mkdtemp()
        try:
            run('touch newfile.txt', cwd=d)
            files = os.listdir(d)
            self.assertEqual(files, ['newfile.txt'])
        finally:
            shutil.rmtree(d)

    def test_expect(self):
        cap = Capture(buffer_size=-1)   # line buffered
        p = run('%s lister.py -d 0.01' % sys.executable,
                async_=True, stdout=cap)
        timeout = 1.0
        m1 = cap.expect('^line 1\r?$', timeout)
        self.assertTrue(m1)
        m2 = cap.expect('^line 5\r?$', timeout)
        self.assertTrue(m2)
        m3 = cap.expect('^line 1.*\r?$', timeout)
        self.assertTrue(m3)
        cap.close(True)
        p.commands[0].kill()
        data = cap.bytes
        self.assertEqual(data[m1.start():m1.end()].rstrip(), b'line 1')
        self.assertEqual(data[m2.start():m2.end()].rstrip(), b'line 5')
        self.assertEqual(data[m3.start():m3.end()].rstrip(), b'line 10')

    def test_redirection_with_whitespace(self):
        node = parse_command_line('a 2 > b')
        self.assertEqual(node.command, ['a', '2'])
        self.assertEqual(node.redirects, {1: ('>', 'b')})
        node = parse_command_line('a 2> b')
        self.assertEqual(node.command, ['a'])
        self.assertEqual(node.redirects, {2: ('>', 'b')})
        node = parse_command_line('a 2 >> b')
        self.assertEqual(node.command, ['a', '2'])
        self.assertEqual(node.redirects, {1: ('>>', 'b')})
        node = parse_command_line('a 2>> b')
        self.assertEqual(node.command, ['a'])
        self.assertEqual(node.redirects, {2: ('>>', 'b')})

    def test_redirection_with_cwd(self):
        workdir = tempfile.mkdtemp()
        try:
            run('echo hello > world', cwd=workdir)
            p = os.path.join(workdir, 'world')
            self.assertTrue(os.path.exists(p))
            with open(p) as f:
                self.assertEqual(f.read().strip(), 'hello')
        finally:
            shutil.rmtree(workdir)

    if sys.platform == 'win32':  #pragma: no cover
        pyrunner_re = re.compile(r'.*py.*\.exe', re.I)
        pywrunner_re = re.compile(r'.*py.*w\.exe', re.I)

        def test_find_command(self):
            cmd = find_command('dummy.py')
            self.assertTrue(cmd is None or pyrunner_re.match(cmd))
            cmd = find_command('dummy.pyw')
            self.assertTrue(cmd is None or pywrunner_re.match(cmd))

        def test_run_found_command(self):
            with open('hello.py', 'w') as f:
                f.write('print("Hello, world!")')
            cmd = find_command('hello')
            if not cmd:
                raise unittest.SkipTest('.py not in PATHEXT or not registered')
            p = capture_stdout('hello')
            self.assertEqual(p.stdout.text.rstrip(), 'Hello, world!')

    def test_feeder(self):
        feeder = Feeder()
        p = capture_stdout([sys.executable, 'echoer.py'], input=feeder,
                           async_=True)
        try:
            lines = ('hello', 'goodbye')
            gen = iter(lines)
            # p.commands may not be set yet (separate thread)
            while not p.commands or p.commands[0].returncode is None:
                logger.debug('commands: %s', p.commands)
                try:
                    data = next(gen)
                except StopIteration:
                    break
                feeder.feed(data + '\n')
                if p.commands:
                    p.commands[0].poll()
                time.sleep(0.05)    # wait for child to return echo
        finally:
            # p.commands may not be set yet (separate thread)
            if p.commands:
                p.commands[0].terminate()
            feeder.close()
        self.assertEqual(p.stdout.text.splitlines(),
                         ['hello hello', 'goodbye goodbye'])

    def test_timeout(self):
        if sys.version_info[:2] < (3, 3):
            raise unittest.SkipTest('test is only valid for Python >= 3.3')
        cap = Capture(buffer_size=1)
        p = run('%s waiter.py 5.0' % sys.executable, async_=True, stdout=cap)
        with self.assertRaises(subprocess.TimeoutExpired):
            p.wait(2.5)
        self.assertEqual(p.returncodes, [None])
        self.assertEqual(cap.read(block=False), b'Waiting ... ')
        p.wait(2.6)  # ensure the child process finishes
        self.assertEqual(p.returncodes, [0])
        expected = b'done.\n' if os.name != 'nt' else b'done.\r\n'
        self.assertEqual(cap.read(), expected)

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
