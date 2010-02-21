import unittest
from urb.colors import colorize

class TestColors(unittest.TestCase):
    def setUp(self): pass
    def tearDown(self): pass

    def testColorize(self):
        '''mIRC colors'''
        self.assertEqual(colorize("Hello <red>world"), "Hello \x035world")
        self.assertEqual(colorize("Hello <white>world"), "Hello \x030world")
        self.assertEqual(colorize("Hello <black>world"), "Hello \x031world")

    def testColorizeNoSuchColor(self):
        '''Some nonexistent colors'''
        greet = "Hello <puce>world"
        self.assertEqual(colorize(greet), greet)

        greet = "Hello <cerulean>world"
        self.assertEqual(colorize(greet), greet)


    def testColorizeSyntax(self):
        '''Syntax cases'''
        # nesting
        greet = "Hello <<red>>world"
        self.assertEqual(colorize(greet), "Hello <\x035>world")
        
        # multiline
        greet = "Hello\n<red>world"
        self.assertEqual(colorize(greet), "Hello\n\x035world")

        # empty token handled ok
        greet = "Hello <>world"
        self.assertEqual(colorize(greet), greet)

        # extra spaces not allowed
        greet = "Hello < red >world"
        self.assertEqual(colorize(greet), greet)

        # case sensitive
        greet = "Hello <RED>world"
        self.assertEqual(colorize(greet), greet)


if __name__ == '__main__':
    unittest.main()
