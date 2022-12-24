import os
import unittest
import sys

import doctest2
from doctest2.util import run_doctest

PROJECT_PATH = os.path.join(os.path.dirname(__file__), '..', '..')

def get_submodules():
    for name in doctest2.__submodules__:
        modname = 'doctest2.%s' % name
        __import__(modname)
        yield sys.modules[modname]

    yield doctest2 # __init__.py

def test_docstrings():
    """Run the doctest strings in doctest2 itself"""
    # Check the doctest2 cases in example (used to be in doctest itself):
    from doctest2.tests import example
    run_doctest(example, verbosity=True) # XXX move example to here
    for sub in get_submodules():
        run_doctest(sub, verbosity=True)

def test_extra_tests():
    """Run the supplementary tests to doctest2 that don't apply to doctest"""
    from doctest2.tests import test_doctest2_shell, test_doctest_additions
    run_doctest(test_doctest2_shell, verbosity=True)
    run_doctest(test_doctest_additions, verbosity=True)

def test_stdlib_tests():
    """Run the doctest strings copied from the stdlib"""
    if 'doctest' in sys.modules:
        raise Exception("doctest already loaded; can't guarantee monkeypatch")
    import doctest, doctest2
    sys.modules['doctest'] = doctest2
    
    from doctest2.tests import test_doctest, test_doctest2
    
    try:
        test_doctest.test_main()
        test_doctest2.test_main()
    finally:
        sys.modules['doctest'] = doctest


def test_main():
    """Basically somewhat like a shell script that runs all the test programs
    
    No effort is made here to unify output or anything. The only reason this
    *isn't* a shell script is coverage reporting.
    """
    test_docstrings()
    test_stdlib_tests()
    test_extra_tests()
    
    unittest.main(argv=['unittest', 'discover', PROJECT_PATH])
    
if __name__ == '__main__':
    test_main()
