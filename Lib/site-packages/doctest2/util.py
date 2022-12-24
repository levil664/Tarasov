import __future__

import sys
import os
import re
import pdb
import traceback
import inspect
import itertools
import tokenize
import subprocess
from functools import reduce
from io import StringIO
from collections import namedtuple
from test import support
from test.support import get_original_stdout

from .constants import *

# TODO: figure out a better place for this
TestResults = namedtuple('TestResults', 'failed attempted')

def _extract_future_flags(globs):
    """
    Return the compiler-flags associated with the future features that
    have been imported into the given namespace (globs).
    """
    flags = 0
    for fname in __future__.all_feature_names:
        feature = globs.get(fname, None)
        if feature is getattr(__future__, fname):
            flags |= feature.compiler_flag
    return flags

def _normalize_module(module, depth=2):
    """
    Return the module specified by `module`.  In particular:
      - If `module` is a module, then return module.
      - If `module` is a string, then import and return the
        module with that name.
      - If `module` is None, then return the calling module.
        The calling module is assumed to be the module of
        the stack frame at the given depth in the call stack.
    """
    if inspect.ismodule(module):
        return module
    elif isinstance(module, str):
        return __import__(module, globals(), locals(), ["*"])
    elif module is None:
        return sys.modules[sys._getframe(depth).f_globals['__name__']]
    else:
        raise TypeError("Expected a module, string, or None")

def _load_testfile(filename, package, module_relative, encoding):
    if module_relative:
        package = _normalize_module(package, 3)
        filename = _module_relative_path(package, filename)
        if hasattr(package, '__loader__'):
            if hasattr(package.__loader__, 'get_data'):
                file_contents = package.__loader__.get_data(filename)
                file_contents = file_contents.decode(encoding)
                # get_data() opens files as 'rb', so one must do the equivalent
                # conversion as universal newlines would do.
                return file_contents.replace(os.linesep, '\n'), filename
    with open(filename, encoding=encoding) as f:
        return f.read(), filename

def _indent(s, indent=4):
    """
    Add the given number of space characters to the beginning of
    every non-blank line in `s`, and return the result.
    """
    # This regexp matches the start of non-blank lines:
    return re.sub('(?m)^(?!$)', indent*' ', s)

def _exception_traceback(exc_info):
    """
    Return a string containing a traceback message for the given
    exc_info tuple (as returned by sys.exc_info()).
    """
    # Get a traceback message.
    excout = StringIO()
    exc_type, exc_val, exc_tb = exc_info
    traceback.print_exception(exc_type, exc_val, exc_tb, file=excout)
    return excout.getvalue()

# Override some StringIO methods.
class _SpoofOut(StringIO):
    def getvalue(self):
        result = StringIO.getvalue(self)
        # If anything at all was written, make sure there's a trailing
        # newline.  There's no way for the expected output to indicate
        # that a trailing newline is missing.
        if result and not result.endswith("\n"):
            result += "\n"
        return result

    def truncate(self, size=None):
        self.seek(size)
        StringIO.truncate(self)

def _comment_line(line):
    "Return a commented form of the given line"
    line = line.rstrip()
    if line:
        return '# '+line
    else:
        return '#'

class _OutputRedirectingPdb(pdb.Pdb):
    """
    A specialized version of the python debugger that redirects stdout
    to a given stream when interacting with the user.  Stdout is *not*
    redirected when traced code is executed.
    """
    def __init__(self, out):
        self.__out = out
        self.__debugger_used = False
        # do not play signal games in the pdb
        pdb.Pdb.__init__(self, stdout=out, nosigint=True)
        # still use input() to get user input
        self.use_rawinput = 1

    def set_trace(self, frame=None):
        self.__debugger_used = True
        if frame is None:
            frame = sys._getframe().f_back
        pdb.Pdb.set_trace(self, frame)

    def set_continue(self):
        # Calling set_continue unconditionally would break unit test
        # coverage reporting, as Bdb.set_continue calls sys.settrace(None).
        if self.__debugger_used:
            pdb.Pdb.set_continue(self)

    def trace_dispatch(self, *args):
        # Redirect stdout to the given stream.
        save_stdout = sys.stdout
        sys.stdout = self.__out
        # Call Pdb's trace dispatch method.
        try:
            return pdb.Pdb.trace_dispatch(self, *args)
        finally:
            sys.stdout = save_stdout

# [XX] Normalize with respect to os.path.pardir?
def _module_relative_path(module, path):
    if not inspect.ismodule(module):
        raise TypeError('Expected a module: %r' % module)
    if path.startswith('/'):
        raise ValueError('Module-relative files may not have absolute paths')

    # Find the base directory for the path.
    if hasattr(module, '__file__'):
        # A normal module/package
        basedir = os.path.split(module.__file__)[0]
    elif module.__name__ == '__main__':
        # An interactive session.
        if len(sys.argv)>0 and sys.argv[0] != '':
            basedir = os.path.split(sys.argv[0])[0]
        else:
            basedir = os.curdir
    else:
        # A module w/o __file__ (this includes builtins)
        raise ValueError("Can't resolve paths relative to the module " +
                         module + " (it has no __file__)")

    # Combine the base directory and the path.
    return os.path.join(basedir, *(path.split('/')))
    

# used in the tests
def run_doctest(module, verbosity=None):
    """Run doctest on the given module. Return (#failures, #tests).
    
    If optional argument verbosity is not specified (or is None), pass
    support's belief about verbosity on to doctest. Else doctest's
    usual behavior is used (it searches sys.argv for -v).
    """
    
    import doctest2
    
    if verbosity is None:
        verbosity = support.verbose
    else:
        verbosity = None
    
    # Direct doctest output (normally just errors) to real stdout; doctest
    # output shouldn't be compared by regrtest.
    save_stdout = sys.stdout
    sys.stdout = get_original_stdout()
    try:
        f, t = doctest2.testmod(module, verbose=verbosity)
        if f:
            raise support.TestFailed("%d of %d doctests failed" % (f, t))
    finally:
        sys.stdout = save_stdout
    if support.verbose:
        print('doctest2 (%s) ... %d tests with zero failures' %
            (module.__name__, t))
    return f, t

def builder(constructor):
    """Create a container using a generator.
    
    The constructor is called with the return value of the decorated function.
        
        >>> from itertools import zip_longest
        >>> @builder(tuple)
        ... def ndim_sub(v1, v2):
        ...     for a, b in zip_longest(v1, v2, fillvalue=0):
        ...         yield a - b
        ...
        >>> ndim_sub((0, 1), (1, 2, 3)) == (-1, -1, -3)
        True
        
    Non-generator return values can be used as well, of course::
        
        >>> from itertools import chain
        >>> s = builder(set)(chain)(["ab"], "cd")
        >>> s == set(['ab', 'c', 'd'])
        True
    
    """
    # should really get added to the builtins
    def decorator(f):
        def g(*args, **kwargs):
            return constructor(f(*args, **kwargs))
        
        return g
    return decorator

class MungingTokenizer(object):
    """
    A tokenizer that never raises exceptions, but always tries to come up with
    a suitable modification to continue tokenizing. The syntax will be invalid,
    so no choice is "correct" -- the goal here is to be able to parse out
    comments, so things like indentation are not considered important.
    
    Unterminated triple-quoted strings their beginning removed and replaced
    with an error token.
    
    Unterminated brackets are left alone, but no exception is raised at the
    end of the file.
    
    All indentation is removed.
    
    Additional lines may be added as part of the error correction process.
    (In particular, every time an unterminated multiline string is found,
    an errortoken and new line are inserted).
    
    None of these matter for the intended use case, which is comment
    extraction from arbitrary attempts at Python code.
    
    """
    MULTILINE_STRING_TOKENS = list(b''.join(t) for t in itertools.product(
        [b'b', b''], [b'r', b''], [b'"""', b"'''"]))
    
    def __init__(self, callable):
        self.callable = callable
        self.lines = []
        self.index = 0
        # we have to increment on the line values we get, because we might
        # restart the tokenizer, and it always thinks it begins at the beginning
        # of a file...
        # TODO: IncrementedTokenizer
        self.line_correction = 0
        self.token_stream = tokenize.tokenize(self.new_callable)
    
    def new_callable(self):
        try:
            return self.lines[self.index]
        except IndexError:
            self.lines.append(self.callable().lstrip(b' \t'))
            return self.lines[self.index]
        finally:
            self.index += 1

    def tokenize(self):
        # Maybe we could actually make dedents go to the nearest indent level,
        # instead of removing all of them?
        while 1:
            # FIXME: remove when 3.2.2 is released
            RESET_TOKENIZER = False; # issue12475 workaround
            try:
                token = next(self.token_stream) # grabs from self.lines
            except tokenize.TokenError as e:
                (msg, (row, col)) = e.args
                row += self.line_correction
                row -= 1 # we start at 0, they don't
                if 'string' in msg:
                    next_token = self.fix_multiline_string(row, col)
                    yield next_token
                    # FIXME: when 3.2.2 is released, call reset_tokenizer here.
                    RESET_TOKENIZER = True
                elif 'statement' in msg:
                    # end of file reached without correct number of closing
                    # brackets.
                    # Since it's the EOF, we are done.
                    yield tokenize.TokenInfo(
                        tokenize.ENDMARKER,
                        '',
                        col,
                        col,
                        row)
                    return
            except StopIteration:
                return
            else:
                yield self.line_corrected_token(token)
            
            if RESET_TOKENIZER:
                self.reset_tokenizer(
                    row, self.lines[row][next_token.end:].lstrip())

    def line_corrected_token(self, token):
        """
        The tokenizer is sometimes restarted, on such occasions its line number
        is set to zero. This method adds back previously read lines to the line
        count.
        """
        ttype, tstring, (srow, scol), (erow, ecol), line = token
        inc = self.line_correction
        return tokenize.TokenInfo(
            ttype,
            tstring,
            (srow + inc, scol),
            (erow + inc, ecol),
            line)

    def reset_tokenizer(self, row, new_startstring):
        self.line_correction += row
        self.index = row + 1
        self.lines.insert(self.index, new_startstring)
        self.token_stream = tokenize.tokenize(self.new_callable)
        next(self.token_stream) # get rid of encoding token

    def fix_multiline_string(self, row, col):
        cur_line = self.lines[row]
        for possible_token in self.MULTILINE_STRING_TOKENS:
            end = col+len(possible_token)
            if cur_line[col:end] == possible_token:
                return tokenize.TokenInfo(
                    tokenize.ERRORTOKEN,
                    possible_token,
                    col,
                    end,
                    row)
        
        for i, line in enumerate(self.lines):
            print(i, '\t', repr(line))
        
        raise AssertionError(
            "MungingTokenizer bug: No error here;" +
            " fix_multiline_string should not have been called",
            row, col, self.lines[row])

def munging_tokenize(callable):
    return MungingTokenizer(callable).tokenize()

def check_program(progname):
    try:
        proc = subprocess.Popen(progname)
    except OSError:
        return False
    else:
        proc.terminate()
        return True
