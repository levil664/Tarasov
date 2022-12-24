import sys

import doctest2

_modules = {}

def patch():
    sys.modules.update(_modules)

def unpatch():
    sys.modules.update({k:v._original for k, v in _modules.items()})

def module(module_obj):
    def decorator(cls):
        _modules[module_obj.__name__] = cls
        return documents(module_obj)(cls)
    return decorator

def documents(obj):
    def decorator(cls):
        cls._original = obj
        return cls
    return decorator

def check(obj):
    attrs = set(dir(cls)) - {'_original'}
    original_attrs = set(dir(cls._original))
    
    new_attrs = attrs - original_attrs
    if new_attrs:
        raise ValueError("New attributes in API doc class %s" % obj, new_attrs)

class ConstantRepr:
    def __init__(self, repr):
        self.repr = repr
    
    def __repr__(self):
        return self.repr
    
    def __str__(self):
        return self.repr

@module(doctest2)
class Doctest2Module:
    @documents(doctest2.testmod)
    def testmod(m=None, name=None, globs=None, verbose=None,
        report=True, optionflags=0, extraglobs=None,
        raise_on_error=False, exclude_empty=False,
        languages=ConstantRepr('doctest2.languages.languages')):
        """
        Test examples in docstrings reachable from module m, starting with
        m.__doc__. Also test examples reachable from dict m.__test__ if it
        exists and is not None.
        
        m.__test__ maps names to functions, classes and strings;
        function and class docstrings are tested even if the name is private;
        strings are tested directly, as if they were docstrings.
        
        :param module m: module to be inspected / tested (defaults to
                         ``__main__``)
        :param str name: name to call module by in reports 
                         (defaults to ``m.__name__``)
        :param dict globs: globals dict used inside doctests (defaults to
                           ``m.__dict__``)
                           
                           Each doctest is run inside a shallow copy of
                           ``globs``. Only used in Python doctests.
        :param dict extraglobs: extra globals to merge into the globals dict
        :param bool verbose: verbosity flag. When true,
                             more report information will be sent to stdout.
                             (defaults to ``'-v' in sys.argv``)
        :param bool report: When true, a summary will be printed at the end.
                            The verbosity of the summary depends on ``verbose``
        :param int optionflags: Options for the doctest runner such as
                                :data:`doctest2.ELLIPSIS` (defaults to ``0``,
                                i.e. no options)
        :param bool raise_on_error: When true, an exception will be raised
                                    if ever a doctest fails or raises an
                                    unexpected exception. This allows for
                                    post-mortem debugging.
        :param bool exclude_empty: When false, empty tests will be generated
                                   for objects with empty docstrings.
        :param language languages: iterable of languages to test
                                   (defaults to all)
        
        :returns: :samp:`({num_failures}, {num_attempts})`
        :rtype: tuple of (int, int)
        
        :raises: doctest2.DocTestFailure when ``raise_on_error`` is enabled
                 and a doctest fails.
        :raises: doctest2.UnexpectedException when ``raise_on_error`` is
                 enabled and a doctest raises an exception that wasn't
                 expected.
        
        """

    @documents(doctest2.testfile)
    def testfile(filename, module_relative=True, name=None, package=None,
             globs=None, verbose=None, report=True, optionflags=0,
             extraglobs=None, raise_on_error=False,
             languages=ConstantRepr('doctest2.languages.languages'),
             encoding=None):
        """
        Test examples in the given file.

        :param str filename: file to be inspected / tested)
        :param str encoding: encoding of file (defaults to ``"utf-8"``)
        :param bool module_relative:
                                    - If True, then the filename is relative to
                                      the current module (or package, if the
                                      package argument is provided).
                                    - If False, the filename is relative to the
                                      current working directory (or absolute)
                                    
                                    (defaults to ``True``)
        :param bool name: name to call file by in reports
                          (defaults to ``m.__name__``)
        :param str package: package used for the base of the filename. If this
                            is provided, then the file is package data.
                            It is an error to provide this argument without
                            ``module_relative`` being True.
        :param dict globs: globals dict used inside doctests (defaults to
                           ``m.__dict__``)
                                   
                           Each doctest is run inside a shallow copy of
                           ``globs``. Only used in Python doctests.
        :param dict extraglobs: extra globals to merge into the globals dict
        :param bool verbose: verbosity flag. When true,
                             more report information will be sent to stdout.
                             (defaults to ``'-v' in sys.argv``)
        :param bool report: When true, a summary will be printed at the end.
                            The verbosity of the summary depends on ``verbose``
        :param int optionflags: Options for the doctest runner such as
                                :data:`doctest2.ELLIPSIS` (defaults to ``0``,
                                i.e. no options)
        :param bool raise_on_error: When true, an exception will be raised
                                    if ever a doctest fails or raises an
                                    unexpected exception. This allows for
                                    post-mortem debugging.
        :param bool exclude_empty: When false, empty tests will be generated
                                   for objects with empty docstrings.
        :param language languages: iterable of languages to test
                                   (defaults to all)
        
        :returns: :samp:`({num_failures}, {num_attempts})`
        :rtype: tuple of (int, int)
        
        :raises: doctest2.DocTestFailure when ``raise_on_error`` is enabled
                 and a doctest fails.
        :raises: doctest2.UnexpectedException when ``raise_on_error`` is
                 enabled and a doctest raises an exception that wasn't
                 expected.
        """


    @documents(doctest2.run_docstring_examples)
    def run_docstring_examples(f, globs, verbose=False, name="NoName",
        compileflags=None, optionflags=0,
        languages=ConstantRepr('doctest2.languages.languages')):
        """
        Test examples in the given object's docstring (`f`), without recursing
        into attributes.
        
        :param object f: Object with a ``__doc__`` atribute to be tested.
        :param dict globs: globals dict used inside doctests (defaults to
                           ``m.__dict__``)
                           
                           Each doctest is run inside a shallow copy of
                           ``globs``. Only used in Python doctests.
        :param dict extraglobs: extra globals to merge into the globals dict
        :param bool verbose: verbosity flag. When true,
                             more report information will be sent to stdout.
                             (defaults to ``'-v' in sys.argv``)
        :param bool name: name to call file by in reports
                          (defaults to ``"NoName"``)
        :param flag compileflags: the set of flags that should be used by the
                                  Python compiler when running the examples.
                                  (defaults to the set of future-import flags
                                  that apply to `globs`.)
        :param int optionflags: Options for the doctest runner such as
                                :data:`doctest2.ELLIPSIS` (defaults to ``0``,
                                i.e. no options)
        :param language languages: iterable of languages to test
                                   (defaults to all)
        
        :returns: :samp:`({num_failures}, {num_attempts})`
        :rtype: tuple of (int, int)
        """