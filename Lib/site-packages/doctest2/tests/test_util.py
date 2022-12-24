import unittest
import tokenize
from io import BytesIO

from doctest2 import util

class TestLineCorrectedToken(unittest.TestCase):
    def setUp(self):
        class TestTokenizer:
            line_corrected_token = classmethod(util.MungingTokenizer.line_corrected_token)
        
        self.tokenizer = TestTokenizer
    
    def testOneLine(self):
        self.tokenizer.line_correction = 0
        orig = tokenize.TokenInfo(
            tokenize.ERRORTOKEN, '"', (1, 0), (1, 1), '"')
        t = self.tokenizer.line_corrected_token(orig)
        
        self.assertEqual(t, orig)
    
    def testSecondLine(self):
        self.tokenizer.line_correction = 1
        self.tokenizer.lines = ['previous line', 'current line']
        orig = tokenize.TokenInfo(
            tokenize.ERRORTOKEN, '"', (1, 0), (1, 1), '"')
        t = self.tokenizer.line_corrected_token(orig)
        
        self.assertEqual(t, tokenize.TokenInfo(
            tokenize.ERRORTOKEN, '"', (2, 0), (2, 1), '"'))

class TokenizerTestCase(unittest.TestCase):
    mtokenizer = lambda self, *args, **kw: util.munging_tokenize(*args, **kw)
    
    otokenizer = lambda self, *args, **kwargs: tokenize.tokenize(*args, **kwargs)
    
    def _convert(self, s):
        return BytesIO(s.encode('ascii')).readline
    
    def sutokenizer(self, s):
        return self.mtokenizer(self._convert(s))
    
    def osutokenizer(self, s):
        return self.otokenizer(self._convert(s))
    
    def rtok(self, t):
        return (t.type, t.string)

@util.builder(list)
def normalize_tokens(t):
    for tok in t:
        if tok.type == tokenize.ERRORTOKEN:
            yield tok.type
        else:
            yield tok.type, tok.string

class TestMultilineSyntaxErrorTokenizing(TokenizerTestCase):
    refstring = "%s4\n1 2 3"
    
    def setUp(self):
        self.errorstring = self.refstring % self.errtoken
        self.ref_tokstream = self.sutokenizer(self.refstring % '"')
        self.new_tokstream = self.sutokenizer(self.errorstring)

class TestMultilineStringErrorTokenizing(TestMultilineSyntaxErrorTokenizing):
    def testCorrectTokenization(self):
        self.assertEqual(
            normalize_tokens(self.ref_tokstream),
            normalize_tokens(self.new_tokstream))


class TestMultilineBracketErrorTokenizing(TestMultilineSyntaxErrorTokenizing):
    def testCorrectTokenization(self):
        self.assertEqual(
            # ignore the coding, error-token, and type of newline
            normalize_tokens(self.ref_tokstream)[4:],
            normalize_tokens(self.new_tokstream)[4:])

class TestOpenParenSyntaxErrorTokenizing(TestMultilineBracketErrorTokenizing):
    errtoken, errclose = "()"

class TestOpenBracketSyntaxErrorTokenizing(TestMultilineBracketErrorTokenizing):
    errtoken, errclose = "[]"

class TestOpenBraceSyntaxErrorTokenizing(TestMultilineBracketErrorTokenizing):
    errtoken, errclose = "{}"

class TestOpenTripleStringSyntaxErrorTokenizing(TestMultilineStringErrorTokenizing):
    errtoken = "'''"

class TestIndentationTokenizing(TokenizerTestCase, unittest.TestCase):
    """
    To prevent indentation errors, the forgiving tokenizer just strips all
    indentation.
    """
    def setUp(self):
        self.errorstring = "a\n  b\n c"
        self.ref_tokstream = self.sutokenizer("a\nb\nc")
        self.new_tokstream = self.sutokenizer(self.errorstring)
    
    def testIndentationStripped(self):
        self.assertEqual(
            list(map(self.rtok, self.ref_tokstream)),
            list(map(self.rtok, self.new_tokstream)))

class ComparativeTokenizerTestCase(TokenizerTestCase):
    def testEqualTokenizing(self):
        ref_tokstream = self.osutokenizer(self.string)
        new_tokstream = self.sutokenizer(self.string)
        
        self.assertEqual(
            list(map(self.rtok, ref_tokstream)),
            list(map(self.rtok, new_tokstream)))

class TestValidMultilineString(ComparativeTokenizerTestCase):
    string = """
'''hello there

'''"""

class TestValidMultilineString(ComparativeTokenizerTestCase):
    string = """\

'''

'''

"""

class TestValidMultilineBrackated(ComparativeTokenizerTestCase):
    string = """
['hello there',
]"""

del TokenizerTestCase, TestMultilineSyntaxErrorTokenizing, TestMultilineStringErrorTokenizing, TestMultilineBracketErrorTokenizing, ComparativeTokenizerTestCase

if __name__ == '__main__':
    unittest.main()
