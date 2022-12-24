import re
import tokenize

import doctest2.languages.python
from . import example, util
from .constants import *

def example_re_from_PS(ps1, ps2):
    return re.compile(r'''
        # Source consists of a PS1 line followed by zero or more PS2 lines.
        (?P<source>
            (?:^(?P<indent> [ ]*) {PS1}    .*)    # PS1 line
            (?:\n           [ ]*  {PS2} .*)*)     # PS2 lines
        \n?
        # Want consists of any non-blank lines that do not start with PS1.
        (?P<want> (?:(?![ ]*$)      # Not a blank line
                     (?![ ]*{PS1})  # Not a line starting with PS1
                     .*$\n?         # But any other line
                  )*)
        '''.format(PS1=re.escape(ps1), PS2=re.escape(ps2)),
        re.MULTILINE | re.VERBOSE)

class DocTestParser:
    """
    A class used to parse strings containing doctest examples.
    """
    
    # This regular expression is used to find doctest examples in a
    # string.  It defines three groups: `source` is the source code
    # (including leading indentation and prompts); `indent` is the
    # indentation of the first (PS1) line of the source code; and
    # `want` is the expected output (including leading indentation).
    def __init__(self, lang=doctest2.languages.python):
        self._EXAMPLE_RE = example_re_from_PS(lang.ps1, lang.ps2)
        self.ps1 = lang.ps1
        self.ps2 = lang.ps2
        self.find_comments = lang.find_comments
        self.language = lang

    # A callable returning a true value iff its argument is a blank line
    # or contains a single comment.
    _IS_BLANK_OR_COMMENT = re.compile(r'^[ ]*(#.*)?$').match

    def parse(self, string, name='<string>'):
        """
        Divide the given string into examples and intervening text,
        and return them as a list of alternating Examples and strings.
        Line numbers for the Examples are 0-based.  The optional
        argument `name` is a name identifying this string, and is only
        used for error messages.
        """
        string = string.expandtabs()
        # If all lines begin with the same indentation, then strip it.
        min_indent = self._min_indent(string)
        if min_indent > 0:
            string = '\n'.join([l[min_indent:] for l in string.split('\n')])

        output = []
        charno, lineno = 0, 0
        # Find all doctest examples in the string:
        for m in self._EXAMPLE_RE.finditer(string):
            # Add the pre-example text to `output`.
            output.append(string[charno:m.start()])
            # Update lineno (lines before this example)
            lineno += string.count('\n', charno, m.start())
            # Extract info from the regexp match.
            (source, options, global_options, want) = \
                     self._parse_example(m, name, lineno)
            # Create an Example, and add it to the list.
            if not self._IS_BLANK_OR_COMMENT(source):
                output.append(example.Example(
                    source,
                    want,
                    lineno=lineno,
                    indent=min_indent+len(m.group('indent')),
                    options=options,
                    global_options=global_options))
            # Update lineno (lines inside this example)
            lineno += string.count('\n', m.start(), m.end())
            # Update charno.
            charno = m.end()
        # Add any remaining post-example text to `output`.
        output.append(string[charno:])
        return output

    def get_doctest(self, string, globs, name, filename, lineno):
        """
        Extract all doctest examples from the given string, and
        collect them into a `DocTest` object.

        `globs`, `name`, `filename`, and `lineno` are attributes for
        the new `DocTest` object.  See the documentation for `DocTest`
        for more information.
        """
        return example.DocTest(self.get_examples(string, name), globs,
                               name, filename, lineno, string,
                               ps1=self.ps1, ps2=self.ps2)

    def get_examples(self, string, name='<string>'):
        """
        Extract all doctest examples from the given string, and return
        them as a list of `Example` objects.  Line numbers are
        0-based, because it's most common in doctests that nothing
        interesting appears on the same line as opening triple-quote,
        and so the first interesting line is called \"line 1\" then.

        The optional argument `name` is a name identifying this
        string, and is only used for error messages.
        """
        return [x for x in self.parse(string, name)
                if isinstance(x, example.Example)]

    def _parse_example(self, m, name, lineno):
        """
        Given a regular expression match from `_EXAMPLE_RE` (`m`),
        return a tuple `(source, options, global_options, want, exc_msg)`,
        where:
        
        - `source` is the matched example's source code (with prompts and
          indentation stripped);
        - `options` are the local options provided as comments
        - `global_options` are the global options provided by comments
        - `want` is the example's expected output (with indentation stripped).
        - `exc_msg` is the exception/error message (if any exists)

        `name` is the string's name, and `lineno` is the line number
        where the example starts; both are used for error messages.
        """
        # Get the example's indentation level.
        indent = len(m.group('indent'))

        # Divide source into lines; check that they're properly
        # indented; and then strip their indentation & prompts.
        source_lines = m.group('source').split('\n')
        
        self._check_prefix(source_lines[1:], ' '*indent + self.ps2, name, lineno)
        self._check_prompt_blank(source_lines, indent, name, lineno)

        source = source_lines[0][indent+len(self.ps1) + 1:] + '\n' + '\n'.join(
            [sl[indent+len(self.ps2) + 1:] for sl in source_lines[1:]])

        # Divide want into lines; check that it's properly indented; and
        # then strip the indentation.  Spaces before the last newline should
        # be preserved, so plain rstrip() isn't good enough.
        want = m.group('want')
        want_lines = want.split('\n')
        if len(want_lines) > 1 and re.match(r' *$', want_lines[-1]):
            del want_lines[-1]  # forget final newline & spaces after it
        self._check_prefix(want_lines, ' '*indent, name,
                           lineno + len(source_lines))
        want = '\n'.join([wl[indent:] for wl in want_lines])

        # Extract options from the source.
        options, global_options = self.find_options(source, name, lineno)

        return source, options, global_options, want

    # This regular expression checks if a comment is an option
    # directive.  Option directives are comments
    # starting with "doctest:".
    _OPTION_DIRECTIVE_RE = re.compile(r'^\s*doctest:\s*([^\'"]*)$')

    def find_options(self, source, name, lineno):
        """
        Return a tuple `(options, global_options)` for option overrides
        extracted from option directives in the given source string.
        `options` is a dict containing the overrides for the current
        Example, and `global_options` is a dict containing the overrides
        for the rest of the doctest.

        `name` is the string's name, and `lineno` is the line number
        where the example starts; both are used for error messages.
        """
        optpair = ({}, {})
        # (note: with the current regexp, this will match at most once:)
        for comment in self.find_comments(source):
            m = self._OPTION_DIRECTIVE_RE.match(comment)
            if m is None:
                continue

            option_strings = m.group(1).replace(',', ' ').split()
            for option in option_strings:
                add_flag = option[0]
                if option[1] == '!':
                    isglobal = True
                    option_name = option[2:]
                else:
                    isglobal = False
                    option_name = option[1:]

                if (add_flag not in '+-' or
                    option_name not in OPTIONFLAGS_BY_NAME):
                    raise ValueError('line %r of the doctest for %s '
                                     'has an invalid option: %r' %
                                     (lineno+1, name, option))

                flag = OPTIONFLAGS_BY_NAME[option_name]
                optpair[isglobal][flag] = (add_flag == '+')
        if optpair[0] and self._IS_BLANK_OR_COMMENT(source):
            # disallow local options because that's obviously a bug,
            # it's pointless.
            # Allow global options because it can be used later in the
            # doctest, not obviously wrong.
            raise ValueError('line %r of the doctest for %s has a local'
                             ' option directive on a line with no example:'
                             ' %r' % (lineno, name, source))
        return optpair

    # This regular expression finds the indentation of every non-blank
    # line in a string.
    _INDENT_RE = re.compile('^([ ]*)(?=\S)', re.MULTILINE)

    def _min_indent(self, s):
        "Return the minimum indentation of any non-blank line in `s`"
        indents = [len(indent) for indent in self._INDENT_RE.findall(s)]
        if len(indents) > 0:
            return min(indents)
        else:
            return 0

    def _check_prompt_blank(self, lines, indent, name, lineno):
        """
        Given the lines of a source string (including prompts and
        leading indentation), check to make sure that every prompt is
        followed by a space character.  If any line is not followed by
        a space character, then raise ValueError.
        """
        ps1 = self.ps1
        ps2 = self.ps2
        for i, line in enumerate(lines):
            dedented = line[indent:]
            if not dedented:
                continue
            
            if dedented.startswith(ps1):
                prefix = ps1
            elif dedented.startswith(ps2):
                prefix = ps2
            else:
                raise ValueError('No prompt prefix provided in line %r of the'
                                 'docstring for %s: %r' %
                                 (lineno+i+1, name, line))
            
            if len(dedented) > len(prefix) and dedented[len(prefix)] != ' ':
                raise ValueError('line %r of the docstring for %s '
                                 'lacks blank after %s: %r' %
                                 (lineno+i+1, name, prefix, line))

    def _check_prefix(self, lines, prefix, name, lineno):
        """
        Check that every line in the given list starts with the given
        prefix; if any line does not, then raise a ValueError.
        """
        for i, line in enumerate(lines):
            if line and not line.startswith(prefix):
                raise ValueError('line %r of the docstring for %s has '
                                 'inconsistent leading whitespace: %r' %
                                 (lineno+i+1, name, line))
