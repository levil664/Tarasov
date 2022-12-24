import unittest

from doctest2 import parse, example

class TestParseEmptyString(unittest.TestCase):
    def test_parse(self):
        parsed = parse.DocTestParser().parse('')
        self.assertEqual(parsed, [''])

class AbstractTestParseSimpleString(object):
    pre_lines = [
        'This is the header:\n',
        '    body (line 1) \n',
        '    body (line 2) \n']
    code_line = 'print(\n'
    code_line2 = '1)\n'
    result_line = '1\n'
    exc_msg = None
    post_lines = [
        '    \n',
        '    This is the, uh, footer\n'
        '    This part of the footer ends without a newline']
    def find_comments(self, *args, **kwargs):
        return []
    
    def setUp(self):
        self.string = (
            ''.join(self.pre_lines) +
                ' '*self.indent + self.ps1 + ' ' + self.code_line +
                ' '*self.indent + self.ps2 + ' ' + self.code_line2 +
                ' '*self.indent + self.result_line +
            ''.join(self.post_lines))
        
        self.parser = parse.DocTestParser(self)
    
    def assertExampleEqual(self, e1, e2):
        self.assertEqual(e1.source, e2.source)
        self.assertEqual(e1.want, e2.want)
        self.assertEqual(e1.lineno, e2.lineno)
        # DELIBERATELY ignoring indent!
        # options doesn't matter
    
    def test_parse(self):
        parsed = self.parser.parse(self.string)
        
        ex = example.Example(
            self.code_line + self.code_line2,
            self.result_line,
            lineno=3)
        
        self.assertEqual(parsed[0], ''.join(self.pre_lines))        
        self.assertExampleEqual(parsed[1], ex)        
        self.assertEqual(parsed[2], ''.join(self.post_lines))

def p_testcase(it, p1, p2):
    class TestCls(AbstractTestParseSimpleString, unittest.TestCase):
        indent = it
        ps1 = p1
        ps2 = p2
    
    TestCls.__name__ = 'Indent%s__%s_%s' % (it, p1, p2)
    
    return TestCls


TestParseSimpleLevelString = p_testcase(4, '>>>', '...')
TestParseSimpleDedentedString = p_testcase(0, '>>>', '...')
TestParseSimpleIndentedString = p_testcase(8, '>>>', '...')

TestParseSimpleLevelString_AltPrefix = p_testcase(4, 'python', 'code')
TestParseSimpleDedentedString_AltPrefix = p_testcase(0, 'python', 'code')
TestParseSimpleIndentedString_AltPrefix = p_testcase(8, 'python', 'code')

TestParseSimpleLevelString_AltShortprefix = p_testcase(4, 'p', 'c')
TestParseSimpleDedentedString_AltShortprefix = p_testcase(0, 'p', 'c')
TestParseSimpleIndentedString_AltShortprefix = p_testcase(8, 'p', 'c')



class AbstractTestParseSimpleExcString(AbstractTestParseSimpleString):
    pass # TODO: this.
