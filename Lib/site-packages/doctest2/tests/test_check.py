import unittest

from doctest2 import example, check, constants

def test_from_desc(t, truth):
    want, got = t
    
    def test_FOO(self):
        self.assertEqual(
            self.checker.check_output(want, got, self.options),
            truth)
    
    return test_FOO

i = 0
def testlist2methlist(tests):
    global i
    for t, truth in tests:
        i += 1
        f = test_from_desc(t, truth)
        f.__name__ = 'test_%s_%s__%s___%s' % (t[0], t[1], truth, i)
        yield f

def convert(cls):
    tests = []
    tests.extend((t, True) for t in cls.true_tests)
    tests.extend((t, False) for t in cls.false_tests)
    
    for func in testlist2methlist(tests):
        fname = func.__name__
        setattr(cls, fname, func)
    
    return cls
    
@convert
class Abstract_CheckerResults(object):
    """test the return values of OutputChecker.check_output()
    
    subclasses should override the class variable "options", and add new test
    cases. All the tests here should pass for *every* option setting.
    
    """
    def setUp(self):
        self.checker = check.OutputChecker()
    
    true_tests = [
        ('1', '1'),
        ('foo', 'foo'),
    ]
    false_tests = [
        ('1', '2'),
        ('foo', 'bar')
    ]

EVAL_PASSING = [
        ('1', '1.0'),
        ('0.0', '-0.0'),
        ('{-1: 1, -2: 1}', '{-2: 1, -1:1}')
    ]

@convert
class TestRegularCheckerResults(Abstract_CheckerResults, unittest.TestCase):
    options = 0
    
    true_tests = []
    false_tests = EVAL_PASSING

@convert
class TestEvalingCheckerResults(Abstract_CheckerResults, unittest.TestCase):
    options = constants.COMPARE_LITERAL_EVAL
    
    true_tests = EVAL_PASSING
    false_tests = [] # can't do NaN :S

    
# we could maybe test more stuff, but the rest is really tested in the
# functional tests already...

if __name__ == '__main__':
    unittest.main()
