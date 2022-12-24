import unittest
import sys
import os
from io import StringIO

from . import run, util
from .run import DocTestRunner
from .parse import DocTestParser
from .find import DocTestFinder
from .constants import *
import doctest2

_unittest_reportflags = 0

class NoTests(Exception):
    """The parser found no tests. This is a problem sometimes."""

def set_unittest_reportflags(flags):
    """Sets the unittest option flags.

    The old flag is returned so that a runner could restore the old
    value if it wished to:
      
      >>> from . import unit # important to use unit module itself
      >>>                    # because of doctest'shandling of globals.
      >>> old = unit._unittest_reportflags
      >>> unit.set_unittest_reportflags(REPORT_NDIFF |
      ...                               REPORT_ONLY_FIRST_FAILURE) == old
      True

      >>> unit._unittest_reportflags == (REPORT_NDIFF |
      ...                                REPORT_ONLY_FIRST_FAILURE)
      True

    Only reporting flags can be set:

      >>> unit.set_unittest_reportflags(ELLIPSIS)
      Traceback (most recent call last):
      ...
      ValueError: ('Only reporting flags allowed', 16)

      >>> unit.set_unittest_reportflags(old) == (REPORT_NDIFF |
      ...                                        REPORT_ONLY_FIRST_FAILURE)
      True
    """
    global _unittest_reportflags

    if (flags & REPORTING_FLAGS) != flags:
        raise ValueError("Only reporting flags allowed", flags)
    old = _unittest_reportflags
    _unittest_reportflags = flags
    return old


class DocTestCase(unittest.TestCase):

    def __init__(self, test, optionflags=0, setUp=None, tearDown=None,
                 checker=None, language=doctest2.languages.python):

        unittest.TestCase.__init__(self)
        self._dt_optionflags = optionflags
        self._dt_checker = checker
        self._dt_test = test
        self._dt_setUp = setUp
        self._dt_tearDown = tearDown
        self._dt_language = language

    def setUp(self):
        test = self._dt_test

        if self._dt_setUp is not None:
            self._dt_setUp(test)

    def tearDown(self):
        test = self._dt_test

        if self._dt_tearDown is not None:
            self._dt_tearDown(test)

        test.globs.clear()

    def runTest(self):
        #import pdb; pdb.set_trace()
        test = self._dt_test
        old = sys.stdout
        new = StringIO()
        optionflags = self._dt_optionflags

        if not (optionflags & REPORTING_FLAGS):
            # The option flags don't include any reporting flags,
            # so add the default reporting flags
            optionflags |= _unittest_reportflags

        runner = DocTestRunner(optionflags=optionflags,
                               checker=self._dt_checker, verbose=False)

        try:
            runner.DIVIDER = "-"*70 # FIXME: that isn't where the divider is...
            runner.run(
                test, out=new.write, clear_globs=False,
                language=self._dt_language)
        finally:
            sys.stdout = old

        if runner.failures:
            raise self.failureException(self.format_failure(new.getvalue()))

    def format_failure(self, err):
        test = self._dt_test
        if test.lineno is None:
            lineno = 'unknown line number'
        else:
            lineno = '%s' % test.lineno
        lname = '.'.join(test.name.split('.')[-1:])
        return ('Failed doctest test for %s\n'
                '  File "%s", line %s, in %s\n\n%s'
                % (test.name, test.filename, lineno, lname, err)
                )

    def debug(self):
        r"""Run the test case without results and without catching exceptions

           The unit test framework includes a debug method on test cases
           and test suites to support post-mortem debugging.  The test code
           is run in such a way that errors are not caught.  This way a
           caller can catch the errors and initiate post-mortem debugging.

           The DocTestCase provides a debug method that raises
           UnexpectedException errors if there is an unexepcted
           exception:
             
             >>> test = DocTestParser().get_doctest('>>> raise KeyError\n42',
             ...                {}, 'foo', 'foo.py', 0)
             >>> case = DocTestCase(test)
             >>> try:
             ...     case.debug()
             ... except run.UnexpectedException as f:
             ...     failure = f

           The UnexpectedException contains the test, the example, and
           the original exception:

             >>> failure.test is test
             True

             >>> failure.example.want
             '42\n'

             >>> exc_info = failure.result.exception
             >>> raise exc_info[1] # Already has the traceback
             Traceback (most recent call last):
             ...
             KeyError

           If the output doesn't match, then a DocTestFailure is raised:

             >>> test = DocTestParser().get_doctest('''
             ...      >>> x = 1
             ...      >>> x
             ...      2
             ...      ''', {}, 'foo', 'foo.py', 0)
             >>> case = DocTestCase(test)
             
             >>> import doctest2
             >>> try:
             ...    case.debug()
             ... except doctest2.DocTestFailure as f:
             ...    failure = f

           DocTestFailure objects provide access to the test:

             >>> failure.test is test
             True

           As well as to the example:

             >>> failure.example.want
             '2\n'

           and the actual output:

             >>> failure.result.to_string()
             '1\n'

           """

        self.setUp()
        runner = run.DebugRunner(optionflags=self._dt_optionflags,
                                 checker=self._dt_checker, verbose=False)
        runner.run(self._dt_test, clear_globs=False, language=self._dt_language)
        self.tearDown()

    def id(self):
        return self._dt_test.name

    def __repr__(self):
        name = self._dt_test.name.split('.')
        return "%s (%s)" % (name[-1], '.'.join(name[:-1]))

    __str__ = __repr__

    def shortDescription(self):
        return "Doctest: " + self._dt_test.name

class SkipDocTestCase(DocTestCase):
    def __init__(self):
        DocTestCase.__init__(self, None)

    def setUp(self):
        self.skipTest("DocTestSuite will not work with -O2 and above")

    def test_skip(self):
        pass

    def shortDescription(self):
        return "Skipping tests from %s" % module.__name__

def DocTestSuite(module=None, globs=None, extraglobs=None,
                 languages=doctest2.languages.languages, **options):
    """
    Convert doctest tests for a module to a unittest test suite.

    This converts each documentation string in a module that
    contains doctest tests to a unittest test case.  If any of the
    tests in a doc string fail, then the test case fails.  An exception
    is raised showing the name of the file containing the test and a
    (sometimes approximate) line number.

    The `module` argument provides the module to be tested.  The argument
    can be either a module or a module name.

    If no argument is given, the calling module is used.

    A number of options may be provided as keyword arguments:

    setUp
      A set-up function.  This is called before running the
      tests in each file. The setUp function will be passed a DocTest
      object.  The setUp function can access the test globals as the
      globs attribute of the test passed.

    tearDown
      A tear-down function.  This is called after running the
      tests in each file.  The tearDown function will be passed a DocTest
      object.  The tearDown function can access the test globals as the
      globs attribute of the test passed.

    globs
      A dictionary containing initial global variables for the tests.

    optionflags
       A set of doctest option flags expressed as an integer.
    """
    
    if sys.flags.optimize >=2:
        # Skip doctests when running with -O2
        suite = unittest.TestSuite()
        suite.addTest(SkipDocTestCase())
        return suite

    module = util._normalize_module(module)
    suite = unittest.TestSuite()
    for language in languages:
        test_finder = DocTestFinder(parser=DocTestParser(language))
        tests = test_finder.find(module, globs=globs, extraglobs=extraglobs)
    
        if not tests:
            # Why do we want to do this? Because it reveals a bug that might
            # otherwise be hidden.
            raise ValueError(module, "has no tests")
        
        tests.sort()
        for test in tests:
            if len(test.examples) == 0:
                continue
            if not test.filename:
                filename = module.__file__
                if filename[-4:] in (".pyc", ".pyo"):
                    filename = filename[:-1]
                test.filename = filename
            suite.addTest(DocTestCase(test, **dict(options, language=language)))
    
    return suite

class DocFileCase(DocTestCase):

    def id(self):
        return '_'.join(self._dt_test.name.split('.'))

    def __repr__(self):
        return self._dt_test.filename
    __str__ = __repr__

    def format_failure(self, err):
        return ('Failed doctest test for %s\n  File "%s", line 0\n\n%s'
                % (self._dt_test.name, self._dt_test.filename, err)
                )

def DocFileTest(path, module_relative=True, package=None,
                globs=None, language=doctest2.languages.python,
                encoding=None, **options):
    if globs is None:
        globs = {}
    else:
        globs = globs.copy()

    if package and not module_relative:
        raise ValueError("Package may only be specified for module-"
                         "relative paths.")

    # Relativize the path.
    doc, path = util._load_testfile(path, package, module_relative,
                               encoding or "utf-8")

    if "__file__" not in globs:
        globs["__file__"] = path

    parser = DocTestParser(language)

    # Find the file and read it.
    name = os.path.basename(path)

    # Convert it to a test, and wrap it in a DocFileCase.
    test = parser.get_doctest(doc, globs, name, path, 0)
    if test.examples:
        return DocFileCase(test, **dict(options, language=language))
    else:
        raise NoTests(test)

def DocFileSuite(*paths, **kw):
    """A unittest suite for one or more doctest files.

    The path to each doctest file is given as a string; the
    interpretation of that string depends on the keyword argument
    "module_relative".

    A number of options may be provided as keyword arguments:

    module_relative
      If "module_relative" is True, then the given file paths are
      interpreted as os-independent module-relative paths.  By
      default, these paths are relative to the calling module's
      directory; but if the "package" argument is specified, then
      they are relative to that package.  To ensure os-independence,
      "filename" should use "/" characters to separate path
      segments, and may not be an absolute path (i.e., it may not
      begin with "/").

      If "module_relative" is False, then the given file paths are
      interpreted as os-specific paths.  These paths may be absolute
      or relative (to the current working directory).

    package
      A Python package or the name of a Python package whose directory
      should be used as the base directory for module relative paths.
      If "package" is not specified, then the calling module's
      directory is used as the base directory for module relative
      filenames.  It is an error to specify "package" if
      "module_relative" is False.

    setUp
      A set-up function.  This is called before running the
      tests in each file. The setUp function will be passed a DocTest
      object.  The setUp function can access the test globals as the
      globs attribute of the test passed.

    tearDown
      A tear-down function.  This is called after running the
      tests in each file.  The tearDown function will be passed a DocTest
      object.  The tearDown function can access the test globals as the
      globs attribute of the test passed.

    globs
      A dictionary containing initial global variables for the tests.

    optionflags
      A set of doctest option flags expressed as an integer.

    languages
      An iterable of doctest languages that will be used to create
      DocFileTests

    encoding
      An encoding that will be used to convert the files to unicode.
    """
    suite = unittest.TestSuite()

    # We do this here so that _normalize_module is called at the right
    # level.  If it were called in DocFileTest, then this function
    # would be the caller and we might guess the package incorrectly.
    if kw.get('module_relative', True):
        kw['package'] = util._normalize_module(kw.get('package'))

    languages = kw.pop('languages', doctest2.languages.languages)

    for path in paths:
        for language in languages:
            try:
                test = DocFileTest(path, **dict(kw, language=language))
            except NoTests as e:
                pass
            else:
                suite.addTest(test)

    return suite
