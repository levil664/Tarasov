import re
import functools
import ast
import fnmatch
from collections import OrderedDict

from .util import check_program

# real constants
HAS_SH = check_program('sh')
HAS_CMD = check_program('cmd')
EXEC_INTERACTIVE_INTERPRETER, EXEC_FRAGMENT = range(2)

OPTIONFLAGS_BY_NAME = {}
OPTIONFLAG_CHECKERS_BY_FLAG = OrderedDict()

def register_optionflag(name):
    # Create a new flag unless `name` is already known.
    return OPTIONFLAGS_BY_NAME.setdefault(name, 1 << len(OPTIONFLAGS_BY_NAME))

def register_optionflag_checker(execute_when):
    """Register an optionflag and associate a checker function with it.
    
    A checker function is called when comparing actual versus specified output.
    These functions are responsible for implementing things such as the
    ELLIPSIS tag. Every checker function has the following form::
    
        @register_optionflag_checker(execute_when=VALUE)
        def OPTIONFLAG_NAME(got, want):
            # ...
            return new_got, new_want, match
    
    execute_when determines when the checker function is called --
    if False, it is called when the flag is NOT turned on. When True, it
    is called when the flag IS turned on.
    
    The name of the function will be the name of the flag as passed to
    register_optionflag. The function will be replaced by the flag it
    checks for.
    
    The function takes two arguments, representing the actual and desired
    output respectively. It returns an iterable of three elements. The first
    two are the new representations of the actual and desired output,
    which will be passed to later checker functions in a pipeline.
    The third iterable is whether or not this checker function found a match.
    
    """
    def decorator(f):
        f.execute_when = execute_when
        flag = register_optionflag(f.__name__)
        OPTIONFLAG_CHECKERS_BY_FLAG[flag] = f
        return flag
    
    return decorator

def pure(f):
    """Decorator shortcut for having checker functions that don't modify inputs
    
    """
    @functools.wraps(f)
    def g(got, want):
        return got, want, f(got, want)
    
    return g

def cram_suffix(suffix):
    """Decorator shortcut for stripping out the cram suffix.
    
    The function is only called if the suffix is present, and then only with
    the suffix stripped out.
    """
    suffix = suffix + '\n'
    def decorator(f):
        @functools.wraps(f)
        def g(got, want):
            if want.endswith(suffix):
                stripped_want = want[:-len(suffix)] + '\n'
                return f(got, stripped_want)
            else:
                return got, want, False
        
        return g
    return decorator

@register_optionflag_checker(execute_when=False)
def DONT_ACCEPT_TRUE_FOR_1(got, want):
    """
    The values True and False replaced 1 and 0 as the return
    value for boolean comparisons in Python 2.3.
    """
    return got, want, ((got,want) == ("True\n", "1\n") or
                       (got,want) == ("False\n", "0\n"))

@register_optionflag_checker(execute_when=False)
def DONT_ACCEPT_BLANKLINE(got, want):
    """
    <BLANKLINE> can be used as a special sequence to signify a
    blank line, unless the DONT_ACCEPT_BLANKLINE flag is used.
    """
    want = re.sub('(?m)^%s\s*?$' % re.escape(BLANKLINE_MARKER),
                  '', want)
    # If a line in got contains only spaces, then remove the
    # spaces.
    got = re.sub('(?m)^\s*?$', '', got)
    
    return got, want, got==want

@register_optionflag_checker(execute_when=True)
def NORMALIZE_WHITESPACE(got, want):
    """
    This flag causes doctest to ignore any differences in the
    contents of whitespace strings.  Note that this can be used
    in conjunction with the ELLIPSIS flag.
    """
    got = ' '.join(got.split())
    want = ' '.join(want.split())
    
    return got, want, got==want

@register_optionflag_checker(execute_when=True)
@pure
def COMPARE_LITERAL_EVAL(got, want):
    """
    This flag causes doctest to use ast.literal_eval to produce an actual
    python object, and compare. In this way, dicts can be more natually
    doctested, and so on.
    """
    try:
        want_value = ast.literal_eval(want)
        got_value = ast.literal_eval(got)
    except ValueError:
        return False
    else:
        return want_value == got_value

# Worst-case linear-time ellipsis matching.
@register_optionflag_checker(execute_when=True)
@pure
def ELLIPSIS(got, want):
    """
    The ELLIPSIS flag says to let the sequence "..." in `want`
    match any substring in `got`.

    Essentially the only subtle case:
    >>> OPTIONFLAG_CHECKERS_BY_FLAG[ELLIPSIS]('aa...aa', 'aaa')[-1]
    False
    """
    if ELLIPSIS_MARKER not in want:
        return want == got

    # Find "the real" strings.
    ws = want.split(ELLIPSIS_MARKER)
    assert len(ws) >= 2

    # Deal with exact matches possibly needed at one or both ends.
    startpos, endpos = 0, len(got)
    w = ws[0]
    if w:   # starts with exact match
        if got.startswith(w):
            startpos = len(w)
            del ws[0]
        else:
            return False
    w = ws[-1]
    if w:   # ends with exact match
        if got.endswith(w):
            endpos -= len(w)
            del ws[-1]
        else:
            return False

    if startpos > endpos:
        # Exact end matches required more characters than we have, as in
        # _ellipsis_match('aa...aa', 'aaa')
        return False

    # For the rest, we only need to find the leftmost non-overlapping
    # match for each piece.  If there's no overall match that way alone,
    # there's no overall match period.
    for w in ws:
        # w may be '' at times, if there are consecutive ellipses, or
        # due to an ellipsis at the start or end of `want`.  That's OK.
        # Search for an empty string succeeds, and doesn't change startpos.
        startpos = got.find(w, startpos, endpos)
        if startpos < 0:
            return False
        startpos += len(w)

    return True

@register_optionflag_checker(execute_when=True)
@pure
def GLOB(got, want):
    return fnmatch.fnmatch(got, want)

@register_optionflag_checker(execute_when=True)
@cram_suffix(' (glob)')
@pure
def CRAM_GLOB(got, want):
    return fnmatch.fnmatch(got, want)

@register_optionflag_checker(execute_when=True)
@pure
def REGEX(got, want):
    return re.match(want, got)

@register_optionflag_checker(execute_when=True)
@cram_suffix(' (re)')
@pure
def CRAM_RE(got, want):
    return re.match(want, got)

SKIP = register_optionflag('SKIP')
IGNORE_EXCEPTION_DETAIL = register_optionflag('IGNORE_EXCEPTION_DETAIL')

COMPARISON_FLAGS = (DONT_ACCEPT_TRUE_FOR_1 |
                    DONT_ACCEPT_BLANKLINE |
                    NORMALIZE_WHITESPACE |
                    ELLIPSIS |
                    SKIP |
                    IGNORE_EXCEPTION_DETAIL |
                    COMPARE_LITERAL_EVAL |
                    GLOB |
                    CRAM_GLOB |
                    REGEX |
                    CRAM_RE)

REPORT_UDIFF = register_optionflag('REPORT_UDIFF')
REPORT_CDIFF = register_optionflag('REPORT_CDIFF')
REPORT_NDIFF = register_optionflag('REPORT_NDIFF')
REPORT_ONLY_FIRST_FAILURE = register_optionflag('REPORT_ONLY_FIRST_FAILURE')

REPORTING_FLAGS = (REPORT_UDIFF |
                   REPORT_CDIFF |
                   REPORT_NDIFF |
                   REPORT_ONLY_FIRST_FAILURE)

# Special string markers for use in `want` strings:
BLANKLINE_MARKER = '<BLANKLINE>'
ELLIPSIS_MARKER = '...'

SUCCESS, FAILURE, BOOM = range(3) # `outcome` state
