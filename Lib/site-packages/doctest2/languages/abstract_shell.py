import os
import shutil
import subprocess
import json

from . import common
from doctest2.constants import *

active = False

# The following two functions rewrite shell examples into something usable.
# The difficulty with shell examples is, how do you figure out when something
# is done? You need to be able to execute one command group at a time and
# analyze the results.
#
# This is done here by grouping commands together with shell-specific grouping
# syntax. The output of the commands is then piped into a command which escapes
# it appropriately.

# MUST work across platforms
FORMAT_COMMAND = 'python3 -m doctest2.scripts._sh_format_output'

# need to do stupid ipc because windows doesn't have signals :(
WAIT_COMMAND = (
    'python3 -m doctest2.scripts._sh_sigskip "%(ipc)s" %(ipc_index)s')

def only_when_examples(f):
    """Only execute a method when self.test.examples is true.
    
    Used as an optimization. Some methods will be undecorated so that they can
    fail loudly if they are called (which should never happen).
    
    """
    def g(self, *args, **kwargs):
        if self.test.examples:
            return f(self, *args, **kwargs)
    return g

class ShellExecutor:
    work_directory = '.doctest2' # TODO: make configurable
    # work_file_name defined in subclasses - a script is used for portability.
    work_file_newline = None
    ipc_file_name = '.doctest2_ipc' # hack for cross-platform signalling
    def __init__(self, test, clear_globs=True, exec_mode=EXEC_INTERACTIVE_INTERPRETER):
        # TODO: clear_globs is bloody useless here. Do shell-specific options.
        self.test = test
        if exec_mode not in [EXEC_INTERACTIVE_INTERPRETER, EXEC_FRAGMENT]:
            raise ValueError(
                "exec_mode must be "
                "EXEC_INTERACTIVE_INTERPRETER or EXEC_FRAGMENT, "
                "got %r instead" % exec_Mode)
    
    @only_when_examples
    def __enter__(self):
        os.mkdir(self.work_directory)
        self.work_file = open(self.work_file_name, 'w',
                              newline=self.work_file_newline)
        self.ipc_file = open(self.ipc_file_name, 'w')
        
        self.last_example_number = -1
        
        self._prepare_script()
        self._prepare_shell()
    
    @only_when_examples
    def __exit__(self, *args):
        self.skip_until(len(self.test.examples))
        self.proc.wait()
        self.ipc_file.close()
        shutil.rmtree(self.work_directory)
        try:
            os.unlink(self.work_file_name)
        except OSError: pass
        try:
            os.unlink(self.ipc_file_name)
        except OSError: pass
    
    def preprocess_source(self, example_source):
        """Preprocess an example's source code to handle incompatibilities
        
        """
        return example_source
    
    def _prepare_script(self):
        """Prepare the shell/batch script that will be run for the tests."""
        for i, example in enumerate(self.test.examples):
            waitcmd = WAIT_COMMAND % dict(
                ipc=os.path.abspath(self.ipc_file_name),
                ipc_index=i)
            
            self.work_file.write(
                self.shell_format % dict(
                    source=self.preprocess_source(example.source),
                    format_command=FORMAT_COMMAND,
                    wait_command=waitcmd))
        
        self.work_file.close()
    
    def _prepare_shell(self):
        self.proc = subprocess.Popen(
            self.shell_command + [os.path.abspath(self.work_file_name)],
            stdout=subprocess.PIPE,
            ##stderr = subprocess.PIPE, # gonna let stderr go.
            stdin = subprocess.PIPE,
            cwd=self.work_directory,
            bufsize=1) # not exactly sure where the buffer is important.
        
        self.proc.stdin.close()
    
    def skip_until(self, examplenum):
        # beautiful beautiful ugly hack
        skipped_range = range(self.last_example_number, examplenum - 1)
        for skipped_example in skipped_range:
            # each of these should be skipped
            self.ipc_file.write('0')
        self.ipc_file.flush()
        for skipped_example in skipped_range:
            # and their output tossed (after a flush so we don't deadlock)
            self.proc.stdout.readline() # empty, because they aren't executed
    
    def execute(self, compileflags, example, examplenum):
        self.skip_until(examplenum)
        self.last_example_number = examplenum

        # this is where we tell it to actually run.
        self.ipc_file.write('1')
        self.ipc_file.flush()
        
        x = str(self.proc.stdout.readline(), 'ascii')
        return common.SimpleOutput(json.loads(x))
