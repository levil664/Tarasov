import pygments

from doctest2.constants import FAILURE, BOOM, SUCCESS

active = False

def comment_finder(lexer, required_start):
    """
    Find and yield all comment strings that start with required_start,
    after stripping that required_start from the string
    
    In particular, the comment character itself should be provided to be
    stripped.
    
        >>> from pygments.lexers import PythonLexer
        >>> print(list(comment_finder(PythonLexer(), '#')('# hello!')))
        [' hello!']
    
    """
    def find_comments(source):
        for tokentype, contents in pygments.lex(source, lexer):
            if tokentype in pygments.token.Comment:
                if contents.startswith(required_start):
                    contents = contents[len(required_start):]
                    yield contents
    
    return find_comments

class SimpleExpectedOutput:
    def __init__(self, stdout):
        self.stdout = stdout

def parse_expected(got):
    return SimpleExpectedOutput(got)

class SimpleOutput:
    def __init__(self, stdout):
        self.stdout = stdout
    
    def to_string(self):
        return self.stdout
    
    def check(self, expected, check_func, optionflags):
        if check_func(expected.stdout, self.stdout, optionflags):
            return SUCCESS
        else:
            return FAILURE
