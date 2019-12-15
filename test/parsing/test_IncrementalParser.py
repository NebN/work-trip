import unittest
from src.parsing import IncrementalParser


class IncrementalParserTests(unittest.TestCase):

    def test_incremental_parser(self):
        ip = IncrementalParser('some 50 users')
        self.assertEqual(ip.extract('(\w+)\s*?(\d+)'), ['some', '50'])
        self.assertEqual(ip.text(), 'users')
        self.assertEqual(ip.extract('(\w+)'), ['users'])
