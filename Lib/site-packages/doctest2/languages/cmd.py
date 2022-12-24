import pygments.formatters, pygments.lexers

from doctest2.constants import HAS_CMD
from .common import parse_expected
from .abstract_shell import ShellExecutor
from .sh import find_comments # ehhhhh

name = 'cmd'
active = HAS_CMD
ps1 = 'cmd>'
ps2 = '?'

class Executor(ShellExecutor):
    work_file_name = '.doctest2_script.bat'
    # Somehow, I thought they'd be more different.
    shell_format = """(
        %(wait_command)s || (
                %(source)s
            ) 2>&1
        ) | %(format_command)s
    
    """
    shell_command = ["cmd", "/Q", "/C"] # don't echo; run command
    
    def preprocess_source(self, source):
        """cmd doesn't support comments, so we strip them out
        
        The Python lexer is used, this is probably good enough."""
        # HACK
        # here we use the sh lexer to lex sh...
        # It'll work, usually, probably.
        #
        # cmd is broken, please don't use it for anything serious. Please!
        # Less broken now than before, sure, but...
        return pygments.format(
            ((type, text) for (type, text) in
                pygments.lex(source, pygments.lexers.BashLexer())
                if type not in pygments.token.Comment),
            pygments.formatters.NullFormatter())
