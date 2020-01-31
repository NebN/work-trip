import unittest
from src.util import collectionutil

class CollectionUtilTest(unittest.TestCase):

    def test(self):
        l = [
            ('123', 1),
            ('123', 2),
            ('123', 3),
            ('45', 4),
            ('45', 5),
            ('6', 6),
            ('', None)
        ]
        res = collectionutil.groupbykey(l)
        print(res)

