#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from os import path
import time
import subprocess
import unittest
from tempfile import NamedTemporaryFile

from wdom.tests.ui.wd import get_wd, free_port


CURDIR = path.dirname(path.abspath(__file__))
ROOTDIR = path.dirname(path.dirname(path.dirname(CURDIR)))

src_aio = '''
import sys
import asyncio

sys.path.append('{rootdir}')

from wdom.misc import install_asyncio
from wdom.tag import H1
from wdom.document import get_document
from wdom.server_aio import get_app, start_server
from wdom.server import exclude_patterns

install_asyncio()
loop = asyncio.get_event_loop()
doc = get_document()
doc.body.appendChild(H1('FIRST', id='h1'))
doc.add_cssfile('testdir/test.css')
app = get_app(doc)
app.add_static_path('testdir', '{curdir}/testdir')
server = start_server(app, loop=loop)
loop.run_forever()
'''.format(rootdir=ROOTDIR, curdir=CURDIR)

css_path = path.join(CURDIR, 'testdir/test.css')
src_css = '''
h1 {color: #000000;}
'''
src_css_post = '''
h1 {color: #ff0000;}
'''

_src = src_aio.splitlines()
src_tornado = '\n'.join(_src).replace('_aio', '_tornado')
src_aio_force_reload = src_aio.replace(
    'get_document()', 'get_document(autoreload=True)')
src_tornado_force_reload = src_tornado.replace(
    'get_document()', 'get_document(autoreload=True)')
_src.insert(12, 'exclude_patterns.append(r\'test.css\')')
src_exclude_css_aio = '\n'.join(_src)
src_exclude_css_tornado = src_exclude_css_aio.replace('_aio', '_tornado')
_src = src_aio.splitlines()
_src.insert(12, 'exclude_patterns.append(r\'testdi*\')')
src_exclude_dir_aio = '\n'.join(_src)
src_exclude_dir_tornado = src_exclude_dir_aio.replace('_aio', '_tornado')


class TestAutoReload(unittest.TestCase):
    def setUp(self):
        with open(css_path, 'w') as f:
            f.write(src_css)
        self.port = free_port()
        self.url = 'http://localhost:{}'.format(self.port)
        tmpfile = NamedTemporaryFile(mode='w+', dir=CURDIR, suffix='.py',
                                     delete=False)
        self.tmpfilename = tmpfile.name
        tmpfile.close()
        self.wd = get_wd()
        self.proc = None

    def tearDown(self):
        if self.proc is not None and self.proc.returncode is None:
            self.proc.terminate()
        if path.exists(self.tmpfilename):
            os.remove(self.tmpfilename)
        with open(css_path, 'w') as f:
            f.write(src_css)

    def _base_args(self):
        return [sys.executable, self.tmpfilename, '--port', str(self.port),
                '--logging', 'error']

    def check_reload(self, args):
        self.proc = subprocess.Popen(args, cwd=CURDIR)
        time.sleep(1)
        self.wd.get(self.url)
        time.sleep(0.1)
        h1 = self.wd.find_element_by_id('h1')
        self.assertEqual(h1.text, 'FIRST')

        with open(self.tmpfilename, 'w') as f:
            f.write(src_aio.replace('FIRST', 'SECOND'))
        time.sleep(1)
        h1 = self.wd.find_element_by_id('h1')
        self.assertEqual(h1.text, 'SECOND')

    def test_autoreload_aio(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_aio)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--autoreload')
        self.check_reload(args)

    def test_autoreload_debug_aio(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_aio)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--debug')
        self.check_reload(args)

    def test_autoreload_force_aio(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_aio_force_reload)
        time.sleep(0.1)
        args = self._base_args()
        self.check_reload(args)

    def test_autoreload_tornado(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_tornado)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--autoreload')
        self.check_reload(args)

    def test_autoreload_debug_tornado(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_tornado)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--debug')
        self.check_reload(args)

    def test_autoreload_force_tornado(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_tornado_force_reload)
        time.sleep(0.1)
        args = self._base_args()
        self.check_reload(args)

    def check_css_reload(self, args):
        self.proc = subprocess.Popen(args, cwd=CURDIR)
        time.sleep(1)
        self.wd.get(self.url)
        time.sleep(0.1)
        h1 = self.wd.find_element_by_id('h1')
        # value_of_css_property return colors as rgba style
        self.assertRegex(h1.value_of_css_property('color'),
                         r'0,\s*0,\s* 0,\s*1\s*')
        with open(css_path, 'w') as f:
            f.write(src_css_post)
        time.sleep(1)
        h1 = self.wd.find_element_by_id('h1')
        self.assertRegex(h1.value_of_css_property('color'),
                         r'255,\s*0,\s* 0,\s*1\s*')

    def test_autoreload_css_aio(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_aio)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--autoreload')
        self.check_css_reload(args)

    def test_autoreload_css_tornado(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_tornado)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--autoreload')
        self.check_css_reload(args)

    def check_css_noreload(self, args):
        self.proc = subprocess.Popen(args, cwd=CURDIR)
        time.sleep(1)
        self.wd.get(self.url)
        time.sleep(0.1)
        h1 = self.wd.find_element_by_id('h1')
        # value_of_css_property return colors as rgba style
        self.assertRegex(h1.value_of_css_property('color'),
                         r'0,\s*0,\s* 0,\s*1\s*')
        with open(css_path, 'w') as f:
            f.write(src_css_post)
        time.sleep(1)
        h1 = self.wd.find_element_by_id('h1')
        self.assertRegex(h1.value_of_css_property('color'),
                         r'0,\s*0,\s* 0,\s*1\s*')

    def test_autoreload_exclude_css_aio(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_exclude_css_aio)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--autoreload')
        self.check_css_noreload(args)

    def test_autoreload_exclude_css_tornado(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_exclude_css_tornado)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--autoreload')
        self.check_css_noreload(args)

    def test_autoreload_exclude_dir_aio(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_exclude_dir_aio)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--autoreload')
        self.check_css_noreload(args)

    def test_autoreload_exclude_dir_tornado(self):
        with open(self.tmpfilename, 'w') as f:
            f.write(src_exclude_dir_tornado)
        time.sleep(0.1)
        args = self._base_args()
        args.append('--autoreload')
        self.check_css_noreload(args)