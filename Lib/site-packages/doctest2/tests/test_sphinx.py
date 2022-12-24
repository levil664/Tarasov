# -*- coding: utf-8 -*-
"""
    test_doctest
    ~~~~~~~~~~~~

    Test the doctest extension.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from io import StringIO
import shutil
import unittest
import os
from functools import wraps

from sphinx import application
from sphinx.ext.autodoc import AutoDirective

from .sphinx_path import path

status = StringIO()
cleanup_called = 0

test_root = path(__file__).parent.joinpath('sphinx_testroot').abspath()

# stuff from sphinx's utils.py
class ListOutput(object):
    """
    File-like object that collects written text in a list.
    """
    def __init__(self, name):
        self.name = name
        self.content = []

    def reset(self):
        del self.content[:]

    def write(self, text):
        self.content.append(text)

class TestApp(application.Sphinx):
    """
    A subclass of :class:`Sphinx` that runs on the test root, with some
    better default values for the initialization parameters.
    """

    def __init__(self, srcdir=None, confdir=None, outdir=None, doctreedir=None,
                 buildername='html', confoverrides=None,
                 status=None, warning=None, freshenv=None,
                 warningiserror=None, tags=None,
                 confname='conf.py', cleanenv=False):

        application.CONFIG_FILENAME = confname

        self.cleanup_trees = [test_root / 'generated']

        if srcdir is None:
            srcdir = test_root
        if srcdir == '(temp)':
            tempdir = path(tempfile.mkdtemp())
            self.cleanup_trees.append(tempdir)
            temproot = tempdir / 'root'
            test_root.copytree(temproot)
            srcdir = temproot
        else:
            srcdir = path(srcdir)
        self.builddir = srcdir.joinpath('_build')
        if confdir is None:
            confdir = srcdir
        if outdir is None:
            outdir = srcdir.joinpath(self.builddir, buildername)
            if not outdir.isdir():
                outdir.makedirs()
            self.cleanup_trees.insert(0, outdir)
        if doctreedir is None:
            doctreedir = srcdir.joinpath(srcdir, self.builddir, 'doctrees')
            if cleanenv:
                self.cleanup_trees.insert(0, doctreedir)
        if confoverrides is None:
            confoverrides = {}
        if status is None:
            status = StringIO.StringIO()
        if warning is None:
            warning = ListOutput('stderr')
        if freshenv is None:
            freshenv = False
        if warningiserror is None:
            warningiserror = False

        application.Sphinx.__init__(self, srcdir, confdir, outdir, doctreedir,
                                    buildername, confoverrides, status, warning,
                                    freshenv, warningiserror, tags)

    def cleanup(self, doctrees=False):
        AutoDirective._registry.clear()
        for tree in self.cleanup_trees:
            shutil.rmtree(tree, True)

def with_app(*args, **kwargs):
    """
    Make a TestApp with args and kwargs, pass it to the test and clean up
    properly.
    """
    def generator(func):
        @wraps(func)
        def deco(self, *args2, **kwargs2):
            app = TestApp(*args, **kwargs)
            func(self, app, *args2, **kwargs2)
            # don't execute cleanup if test failed
            app.cleanup()
        return deco
    return generator

# end stuff from utils.py

#@unittest.FunctionTestCase
class TestDoctestBuild(unittest.TestCase):
    @with_app(buildername='doctest', status=status)
    def test_build(self, app):
        reset_called()
        app.builder.build_all()
        if app.statuscode != 0:
            print(status.getvalue(), file=sys.stderr)
            self.fail('failures in doctests')
        # in doctest.txt, there are two named groups and the default group,
        # so the cleanup function must be called three times
        self.assertEqual(get_called(), 3, 
            'testcleanup did not get executed enough times')

def cleanup_call():
    from doctest2.tests import test_sphinx
    test_sphinx.cleanup_called += 1

def get_called():
    from doctest2.tests import test_sphinx
    return test_sphinx.cleanup_called

def reset_called():
    from doctest2.tests import test_sphinx
    test_sphinx.cleanup_called = 0

#import pdb; pdb.set_trace()

if __name__ == '__main__':
    unittest.main()
