import unittest

from doctest2 import example

class Abstract_ExampleSanitizesInput(object):
    """test that example sanitizes ``source`` and ``want`` correctly.
    
    All subclasses do is set a self.srcend and self.wantend to a newline or
    empty string, to cover all variations.
    
    """
    def setUp(self):
        self.example = example.Example(
            "a = 2" + self.srcend,
            "2" + self.wantend)
    
    def test_sourceNewline(self):
        self.assertEqual(self.example.source, 'a = 2\n')
    
    def test_wantNewline(self):
        self.assertEqual(self.example.want, '2\n')

class TestExampleSanitizesNonewline(Abstract_ExampleSanitizesInput, unittest.TestCase):
    srcend = wantend = ''

class TestExampleSanitizesNewline(Abstract_ExampleSanitizesInput, unittest.TestCase):
    srcend = wantend = '\n'

class TestExampleSanitizesEmptyString(unittest.TestCase):
    def setUp(self):
        self.example = example.Example("", "")
    
    def test_sourceDoesntStayEmpty(self):
        self.assertEqual(self.example.source, '\n')
    
    def test_wantStaysEmpty(self):
        self.assertEqual(self.example.want, '')
    
    
# we could maybe test more stuff, but this is all that's worth testing.

if __name__ == '__main__':
    unittest.main()
