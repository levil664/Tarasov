# Module doctest2.
# Licensed under the MIT License (see LICENSE file)
# Based on doctest, which was released to the public domain 16-Jan-2001,
#     by Tim Peters (tim@python.org).
# Major enhancements and refactoring by:
#     Jim Fulton
#     Edward Loper
# doctest2 enhancements and refactoring by:
#     Devin Jeanpierre

r"""Module doctest -- a framework for running examples in docstrings.

In simplest use, end each module M to be tested with:

def _test():
    import doctest2
    doctest2.testmod()

if __name__ == "__main__":
    _test()

Then running the module as a script will cause the examples in the
docstrings to get executed and verified:

python M.py

This won't display anything unless an example fails, in which case the
failing example(s) and the cause(s) of the failure(s) are printed to stdout
(why not stderr? because stderr is a lame hack <0.2 wink>), and the final
line of output is "Test failed.".

Run it with the -v switch instead:

python M.py -v

and a detailed report of all examples tried is printed to stdout, along
with assorted summaries at the end.

You can force verbose mode by passing "verbose=True" to testmod, or prohibit
it by passing "verbose=False".  In either of those cases, sys.argv is not
examined by testmod.

There are a variety of other ways to run doctests, including integration
with the unittest framework, and support for running non-Python text
files containing doctests.  There are also many ways to override parts
of doctest2's default behaviors.  See the Library Reference Manual for
details.
"""

__docformat__ = 'reStructuredText en'

from .constants import *
from .example import Example, DocTest
from .parse import DocTestParser
from .find import DocTestFinder
from .run import DocTestRunner, DocTestFailure, UnexpectedException, DebugRunner
from .check import OutputChecker
from .test import testmod, testfile, run_docstring_examples
from .unit import DocTestSuite, DocFileSuite, set_unittest_reportflags
from .debug import script_from_examples, testsource, debug, debug_src

__submodules__ = [
# I don't know, it's a hack for testing. Like __all__, but without all the
# classes and stuff.

######################################################################
## Table of Contents
######################################################################
#  1. Utility Functions
        'util',
#  2. Example & DocTest -- store test cases
        'example',
#  3. DocTest Parser -- extracts examples from strings
        'parse',
#  4. DocTest Finder -- extracts test cases from objects
        'find',
#  5. DocTest Runner -- runs test cases
        'run',
        'check',
#  6. Test Functions -- convenient wrappers for testing
        'test',
#  7. Unittest Support
        'unit',
#  8. Debugging Support
        'debug',
#  9. Sphinx Support
        'sphinx_ext',
]
