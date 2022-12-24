import re
import sys
import pdb
import traceback
from io import StringIO

import doctest2.languages
from . import util, check
from .util import TestResults
from .check import OutputChecker
from .constants import *



class DocTestReporter:
    # This divider string is used to separate failure messages, and to
    # separate sections of the summary.
    DIVIDER = "*" * 70
    
    def __init__(self, write, verbose=False):
        self.write = write
        self.verbose = verbose

    #/////////////////////////////////////////////////////////////////
    # Reporting methods
    #/////////////////////////////////////////////////////////////////

    def report_start(self, _optionflags, test, example):
        """
        Report that the test runner is about to process the given
        example.  (Only displays a message if verbose=True)
        """
        if self.verbose:
            if example.want:
                self.write('Trying:\n' + util._indent(example.source) +
                           'Expecting:\n' + util._indent(example.want))
            else:
                self.write('Trying:\n' + util._indent(example.source) +
                           'Expecting nothing\n')

    def report_success(self, _optionflags, _test, _example, _result):
        """
        Report that the given example ran successfully.  (Only
        displays a message if verbose=True)
        """
        if self.verbose:
            self.write("ok\n")

    def report_failure(self, optionflags, test, example, result):
        """
        Report that the given example failed.
        """
        self.write(self._failure_header(test, example) +
            check.output_difference(example, result.to_string(), optionflags))

    def report_unexpected_exception(self, _optflags, test, example, result):
        """
        Report that the given example raised an unexpected exception.
        """
        self.write(self._failure_header(test, example) +
            'Exception raised:\n' + util._indent(result.to_traceback()))

    def _failure_header(self, test, example):
        out = [self.DIVIDER]
        if test.filename:
            if test.lineno is not None and example.lineno is not None:
                lineno = test.lineno + example.lineno + 1
            else:
                lineno = '?'
            out.append('File "%s", line %s, in %s' %
                       (test.filename, lineno, test.name))
        else:
            out.append('Line %s, in %s' % (example.lineno+1, test.name))
        out.append('Failed example:')
        source = example.source
        out.append(util._indent(source))
        return '\n'.join(out)

class DocTestRunner:
    """
    A class used to run DocTest test cases, and accumulate statistics.
    The `run` method is used to process a single DocTest case.  It
    returns a tuple `(f, t)`, where `t` is the number of test cases
    tried, and `f` is the number of test cases that failed.
    
        >>> from .find import DocTestFinder
        >>> from .tests.example import _TestClass
        >>> tests = DocTestFinder().find(_TestClass)
        >>> runner = DocTestRunner(verbose=False)
        >>> tests.sort(key = lambda test: test.name)
        >>> for test in tests:
        ...     print(test.name, '->', runner.run(test))
        _TestClass -> TestResults(failed=0, attempted=2)
        _TestClass.__init__ -> TestResults(failed=0, attempted=2)
        _TestClass.get -> TestResults(failed=0, attempted=2)
        _TestClass.square -> TestResults(failed=0, attempted=1)

    The `summarize` method returns a summary of all the test cases that
    have been run by the runner:

        >>> print(runner.summarize(verbose=1), end='')
        4 items passed all tests:
           2 tests in _TestClass
           2 tests in _TestClass.__init__
           2 tests in _TestClass.get
           1 tests in _TestClass.square
        7 tests in 4 items.
        7 passed and 0 failed.
        Test passed.

    The aggregated number of tried examples and failed examples is
    available via the `tries` and `failures` attributes:

        >>> runner.tries
        7
        >>> runner.failures
        0

    The comparison between expected outputs and actual outputs is done
    by an `OutputChecker`.  This comparison may be customized with a
    number of option flags; see the documentation for `testmod` for
    more information.  If the option flags are insufficient, then the
    comparison may also be customized by passing a subclass of
    `OutputChecker` to the constructor.

    The test runner's display output can be controlled in two ways.
    First, an output function (`out) can be passed to
    `TestRunner.run`; this function will be called with strings that
    should be displayed.  It defaults to `sys.stdout.write`.  If
    capturing the output is not sufficient, then the display output
    can be also customized by subclassing DocTestReporter, and
    overriding the methods `report_start`, `report_success`,
    `report_unexpected_exception`, and `report_failure`. The new
    reporter class can be passed to DocTestRunner.
    """

    def __init__(self,
                 checker=None,
                 verbose=None,
                 optionflags=0,
                 reporter_cls=DocTestReporter):
        """
        Create a new test runner.

        Optional keyword arg `checker` is the `OutputChecker` that
        should be used to compare the expected outputs and actual
        outputs of doctest examples.

        Optional keyword arg 'verbose' prints lots of stuff if true,
        only failures if false; by default, it's true iff '-v' is in
        sys.argv.

        Optional argument `optionflags` can be used to control how the
        test runner compares expected output to actual output, and how
        it displays failures.  See the documentation for `testmod` for
        more information.
        """
        self._checker = checker or OutputChecker()
        if verbose is None:
            verbose = '-v' in sys.argv # EW
        self._verbose = verbose
        self.optionflags = optionflags
        self.original_optionflags = optionflags

        # Keep track of the examples we've run.
        self.tries = 0
        self.failures = 0
        self._name2ft = {}
        
        # Store the reporter class used for formatting output
        self.reporter_cls = reporter_cls

    #/////////////////////////////////////////////////////////////////
    # DocTest Running
    #/////////////////////////////////////////////////////////////////

    def _record_outcome(self, test, f, t):
        """
        Record the fact that the given DocTest (`test`) generated `f`
        failures out of `t` tried examples.
        """
        f2, t2 = self._name2ft.get(test.name, (0,0))
        self._name2ft[test.name] = (f+f2, t+t2)
        self.failures += f
        self.tries += t

    def _run(self, test, compileflags, reporter, language, execer):
        """
        Run the examples in `test`.  Write the outcome of each example
        with one of the `DocTestRunner.report_*` methods, using the
        reporter object `reporter`.  `compileflags` is the set of compiler
        flags that should be used to execute examples.  Return a tuple
        `(f, t)`, where `t` is the number of examples tried, and `f`
        is the number of examples that failed.  The examples are run
        in the namespace `test.globs`.
        """
        # Keep track of the number of failures and tries.
        failures = tries = 0

        check = self._checker.check_output

        # some options are retained in-between examples.
        global_optionflags = 0

        # Process each example.
        for examplenum, example in enumerate(test.examples):
            optionflags = self.optionflags

            # If REPORT_ONLY_FIRST_FAILURE is set, then supress
            # reporting after the first failure.
            quiet = (optionflags & REPORT_ONLY_FIRST_FAILURE and
                     failures > 0)

            if example.global_options:
                for (optionflag, val) in example.global_options.items():
                    if val:
                        global_optionflags |= optionflag
                    else:
                        global_optionflags &= ~optionflag

            optionflags |= global_optionflags

            if example.options:
                for (optionflag, val) in example.options.items():
                    if val:
                        optionflags |= optionflag
                    else:
                        optionflags &= ~optionflag

            # If 'SKIP' is set, then skip this example.
            if optionflags & SKIP:
                continue

            # Record that we started this example.
            tries += 1
            if not quiet:
                reporter.report_start(optionflags, test, example)

            result = execer.execute(compileflags, example, examplenum)
            expected = language.parse_expected(example.want)
            outcome = result.check(expected, check, optionflags)

            # Report the outcome.
            if outcome is SUCCESS:
                if not quiet:
                    reporter.report_success(optionflags, test, example, result)
            elif outcome is FAILURE:
                if not quiet:
                    reporter.report_failure(optionflags, test, example, result)
                failures += 1
            elif outcome is BOOM:
                if not quiet:
                    reporter.report_unexpected_exception(optionflags,
                                                         test,
                                                         example,
                                                         result) # ew
                failures += 1
            else:
                raise AssertionError("unknown outcome", outcome)

        # Record and return the number of failures and tries.
        self._record_outcome(test, failures, tries)
        return TestResults(failures, tries)

    def run(self, test, compileflags=None, out=None, clear_globs=True,
            exec_mode=EXEC_INTERACTIVE_INTERPRETER,
            language=doctest2.languages.python):
        """
        Run the examples in `test`, and display the results using the
        writer function `out`.

        The examples are run in the namespace `test.globs`.  If
        `clear_globs` is true (the default), then this namespace will
        be cleared after the test runs, to help with garbage
        collection.  If you would like to examine the namespace after
        the test completes, then use `clear_globs=False`.

        `compileflags` gives the set of flags that should be used by
        the Python compiler when running the examples.  If not
        specified, then it will default to the set of future-import
        flags that apply to `globs`.

        The output of each example is checked using
        `DocTestRunner.check_output`, and the results are formatted by
        the `DocTestRunner.report_*` methods.
        """
        if compileflags is None:
            compileflags = util._extract_future_flags(test.globs)

        save_stdout = sys.stdout
        if out is None:
            encoding = save_stdout.encoding
            if encoding is None or encoding.lower() == 'utf-8':
                out = save_stdout.write
            else:
                # Use backslashreplace error handling on write
                def out(s):
                    s = str(s.encode(encoding, 'backslashreplace'), encoding)
                    save_stdout.write(s)
        reporter = self.reporter_cls(out, verbose=self._verbose)

        execer = language.Executor(test,
                                   clear_globs=clear_globs,
                                   exec_mode=EXEC_INTERACTIVE_INTERPRETER)

        with execer:
            return self._run(test, compileflags, reporter, language, execer)

    #/////////////////////////////////////////////////////////////////
    # Summarization
    #/////////////////////////////////////////////////////////////////
    def summarize(self, verbose=None):
        """
        Print a summary of all the test cases that have been run by
        this DocTestRunner (`runner`)
        """
        # No reason to be in reporter.
        if verbose is None:
            verbose = self._verbose
        notests = []
        passed = []
        failed = []
        totalt = totalf = 0
        out = StringIO()
        def o_print(*args, **kwargs):
            kwargs['file'] = out
            return print(*args, **kwargs)
        
        for x in self._name2ft.items():
            name, (f, t) = x
            assert f <= t
            totalt += t
            totalf += f
            if t == 0:
                notests.append(name)
            elif f == 0:
                passed.append( (name, t) )
            else:
                failed.append(x)
        if verbose:
            if notests:
                o_print(len(notests), "items had no tests:")
                notests.sort()
                for thing in notests:
                    o_print("   ", thing)
            if passed:
                o_print(len(passed), "items passed all tests:")
                passed.sort()
                for thing, count in passed:
                    o_print(" %3d tests in %s" % (count, thing))
        if failed:
            o_print(self.reporter_cls.DIVIDER)
            o_print(len(failed), "items had failures:")
            failed.sort()
            for thing, (f, t) in failed:
                o_print(" %3d of %3d in %s" % (f, t, thing))
        if verbose:
            o_print(totalt, "tests in", len(self._name2ft), "items.")
            o_print(totalt - totalf, "passed and", totalf, "failed.")
        if totalf:
            o_print("***Test Failed***", totalf, "failures.")
        elif verbose:
            o_print("Test passed.")
        assert totalt == self.tries
        assert totalf == self.failures
        
        return out.getvalue()

    #/////////////////////////////////////////////////////////////////
    # Backward compatibility cruft to maintain doctest.master.
    #/////////////////////////////////////////////////////////////////
    def merge(self, other):
        d = self._name2ft
        for name, (f, t) in other._name2ft.items():
            if name in d:
                # Don't print here by default, since doing
                #     so breaks some of the buildbots
                #print("*** DocTestRunner.merge: '" + name + "' in both" \
                #    " testers; summing outcomes.")
                f2, t2 = d[name]
                f = f + f2
                t = t + t2
            d[name] = f, t

class DocTestFailure(Exception):
    """A DocTest example has failed in debugging mode.

    The exception instance has variables:

    - test: the DocTest object being run

    - example: the Example object that failed

    - got: the actual output
    """
    def __init__(self, test, example, result):
        self.test = test
        self.example = example
        self.result = result

    def __str__(self):
        return str(self.test)

# Debug running/reportng

class DebugDocTestReporterMixin:
    def report_unexpected_exception(self, _optflags, test, example, result_err):
        raise UnexpectedException(test, example, result_err)

    def report_failure(self, _optflags, test, example, result):
        raise DocTestFailure(test, example, result)

class DebugDocTestReporter(DebugDocTestReporterMixin, DocTestReporter):
    pass

class UnexpectedException(Exception):
    """A DocTest example has encountered an unexpected exception

    The exception instance has variables:

    - test: the DocTest object being run

    - example: the Example object that failed

    - exc_info: the exception info
    """
    def __init__(self, test, example, result):
        self.test = test
        self.example = example
        self.result = result

    def __str__(self):
        return str(self.test)

class DebugRunner(DocTestRunner):
    r"""Run doc tests but raise an exception as soon as there is a failure.

       This is achieved through a new default test reporter, DebugTestReporter.
       To add the functionality to your own test reporter, use the
       DebugTestReporterMixin mixin.

       If an unexpected exception occurs, an UnexpectedException is raised.
       It contains the test, the example, and the original exception:
        
         >>> from .parse import DocTestParser
         >>> runner = DebugRunner(verbose=False)
         >>> test = DocTestParser().get_doctest('>>> raise KeyError\n42',
         ...                                    {}, 'foo', 'foo.py', 0)
         >>> try:
         ...     runner.run(test)
         ... except UnexpectedException as f:
         ...     failure = f

         >>> failure.test is test
         True

         >>> failure.example.want
         '42\n'

         >>> exc_info = failure.result.exception
         >>> raise exc_info[1] # Already has the traceback
         Traceback (most recent call last):
         ...
         KeyError

       We wrap the original exception to give the calling application
       access to the test and example information.

       If the output doesn't match, then a DocTestFailure is raised:
         
         >>> from .parse import DocTestParser
         >>> test = DocTestParser().get_doctest('''
         ...      >>> x = 1
         ...      >>> x
         ...      2
         ...      ''', {}, 'foo', 'foo.py', 0)

         >>> try:
         ...    runner.run(test)
         ... except DocTestFailure as f:
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

       If a failure or error occurs, the globals are left intact:

         >>> del test.globs['__builtins__']
         >>> test.globs
         {'x': 1}

         >>> from .parse import DocTestParser
         >>> test = DocTestParser().get_doctest('''
         ...      >>> x = 2
         ...      >>> raise KeyError
         ...      ''', {}, 'foo', 'foo.py', 0)

         >>> runner.run(test) #doctest: +IGNORE_EXCEPTION_DETAIL
         Traceback (most recent call last):
         ...
         doctest2.UnexpectedException: <DocTest foo from foo.py:0 (2 examples)>

         >>> del test.globs['__builtins__']
         >>> test.globs
         {'x': 2}

       But the globals are cleared if there is no error:

         >>> from .parse import DocTestParser
         >>> test = DocTestParser().get_doctest('''
         ...      >>> x = 2
         ...      ''', {}, 'foo', 'foo.py', 0)

         >>> runner.run(test)
         TestResults(failed=0, attempted=1)

         >>> test.globs
         {}

       """

    def __init__(self,
                 checker=None,
                 verbose=None,
                 optionflags=0,
                 reporter_cls=DebugDocTestReporter):
        super(DebugRunner, self).__init__(checker=checker,
                                          verbose=verbose,
                                          optionflags=optionflags,
                                          reporter_cls=reporter_cls)

    def run(self, test, compileflags=None, out=None, clear_globs=True,
            language=doctest2.languages.python):
        r = DocTestRunner.run(self, test, compileflags, out, False)
        if clear_globs:
            test.globs.clear()
        return r
