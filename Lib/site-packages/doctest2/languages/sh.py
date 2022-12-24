import subprocess
import binascii
from pygments.lexers import BashLexer

from doctest2.constants import HAS_SH
from .abstract_shell import ShellExecutor
from .common import comment_finder, parse_expected

name = 'sh'
active = HAS_SH
ps1 = '$'
ps2 = '>'
find_comments = comment_finder(BashLexer(), '#')

class Executor(ShellExecutor):
    work_file_name = '.doctest2_script.sh'
    # apparently this matters on Windows:
    # msysgit works fine even with \r\n, but cygwin wants \n
    work_file_newline = '\n'
    shell_format = """{
        %(wait_command)s || {
                %(source)s
            } 2>&1
        } | %(format_command)s
    
    """
    shell_command = ["sh"]
    
    def preprocess_source(self, source):
        """
        Since all the source lines are concatenated into one big file,
        it's possible for syntax errors in one entry to ruin the entire test.
        
        Thankfully, there's a way out: each entry can be checked for validity
        with sh -n, and if it isn't valid, the entry will be replaced with
        an instruction to print out the error message. This doesn't match the
        behavior of the interactive shell, but it seems pretty reasonable.
        Indeed, Python doctests differ from the real interactive interpreter
        in the same way. In the real world, if you leave off a trailing quote,
        both will wait forever for the trailing quote. But in doctests, it
        will pretend parsing is cut off at the end of the source.
        So we get:
        
            >>> '''
            Traceback (most recent call last):
             ...
            SyntaxError: EOF while scanning triple-quoted string literal
        
        and similarly for posix shells.
        
            $ echo " # doctest: +ELLIPSIS
            ...
            $ # the above is some shell-specific error message
        
        """
        check_proc = subprocess.Popen(
            self.shell_command + ["-n"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        
        stdout, stderr = check_proc.communicate(source.encode('utf-8'))
        exit = check_proc.returncode
        
        if exit == 0:
            return source
        else:
            return 'python3 -m doctest2.scripts._print %s %s' % (
                binascii.hexlify(stdout + stderr), exit)
