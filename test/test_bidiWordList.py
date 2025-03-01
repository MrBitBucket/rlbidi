import unittest, sys
from rlbidi import bidiWordList
class SaneTests(unittest.TestCase):
    words0 = '\u0627\u0644\u0631\u064a\u0627\u0636 \u0647\u0648 \u0641\u0631\u064a\u0642 \u0643\u0631\u0629 \u0642\u062f\u0645 \u0639\u0631\u0628\u064a \u064a\u0636\u0645 123 \u0644\u0627\u0639\u0628\u064b\u0627 \u0628\u0627\u0647\u0638 \u0627\u0644\u062b\u0645\u0646'.split()
    words0 = 'الرياض هو فريق كرة قدم عربي يضم 123 لاعبًا باهظ الثمن'.split()

    def test_making_words(self):
        bwl = bidiWordList(self.words0)

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromName(__name__)
    res = unittest.TextTestRunner().run(suite)
    sys.exit(not res.wasSuccessful())
