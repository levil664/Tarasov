######################################################################
## 2. Example & DocTest
######################################################################
## - An "example" is a <source, want> pair, where "source" is a
##   fragment of source code, and "want" is the expected output for
##   "source."  The Example class also includes information about
##   where the example was extracted from.
##
## - A "doctest" is a collection of examples, typically extracted from
##   a string (such as an object's docstring).  The DocTest class also
##   includes information about where the string was extracted from.

class Example:
    """
    A single doctest example, consisting of source code and expected
    output.  `Example` defines the following attributes:

      - source: A Python statement, always ending with a newline.
        The constructor adds a newline if needed.

      - want: The expected output from running the source code (either
        from stdout, or a traceback in case of exception).  `want` ends
        with a newline unless it's empty, in which case it's an empty
        string.  The constructor adds a newline if needed.

      - lineno: The line number within the DocTest string containing
        this Example where the Example begins.  This line number is
        zero-based, with respect to the beginning of the DocTest.

      - indent: The example's indentation in the DocTest string.
        I.e., the number of space characters that preceed the
        example's first prompt.

      - options: A dictionary mapping from option flags to True or
        False, which is used to override default options for this
        example.  Any option flags not contained in this dictionary
        are left at their default value (as specified by the
        DocTestRunner's optionflags).  By default, no options are set.
    """
    def __init__(self, source, want, lineno=0, indent=0,
                 options=None, global_options=None):
        # Normalize inputs.
        if not source.endswith('\n'):
            source += '\n'
        if want and not want.endswith('\n'):
            want += '\n'
        # Store properties.
        self.source = source
        self.want = want
        self.lineno = lineno
        self.indent = indent
        if options is None: options = {}
        self.options = options
        if global_options is None: global_options = {}
        self.global_options = global_options

class DocTest:
    """
    A collection of doctest examples that should be run in a single
    namespace.  Each `DocTest` defines the following attributes:

      - examples: the list of examples.

      - globs: The namespace (aka globals) that the examples should
        be run in.

      - name: A name identifying the DocTest (typically, the name of
        the object whose docstring this DocTest was extracted from).

      - filename: The name of the file that this DocTest was extracted
        from, or `None` if the filename is unknown.

      - lineno: The line number within filename where this DocTest
        begins, or `None` if the line number is unavailable.  This
        line number is zero-based, with respect to the beginning of
        the file.

      - docstring: The string that the examples were extracted from,
        or `None` if the string is unavailable.
    """
    def __init__(self, examples, globs, name, filename, lineno, docstring,
                 ps1=None, ps2=None):
        """
        Create a new DocTest containing the given examples.  The
        DocTest's globals are initialized with a copy of `globs`.
        """
        assert not isinstance(examples, str), \
               "DocTest no longer accepts str; use DocTestParser instead"
        self.examples = examples
        self.docstring = docstring
        self.globs = globs.copy()
        self.name = name
        self.filename = filename
        self.lineno = lineno
        self.ps1 = ps1
        self.ps2 = ps2

    def __repr__(self):
        if len(self.examples) == 0:
            examples = 'no examples'
        elif len(self.examples) == 1:
            examples = '1 example'
        else:
            examples = '%d examples' % len(self.examples)
        return ('<DocTest %s from %s:%s (%s)>' %
                (self.name, self.filename, self.lineno, examples))


    # This lets us sort tests by name:
    def __lt__(self, other):
        if not isinstance(other, DocTest):
            return NotImplemented
        return ((self.name, self.filename, self.lineno, id(self))
                <
                (other.name, other.filename, other.lineno, id(other)))
