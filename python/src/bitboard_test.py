import unittest
from bitboard import BitBoard

class TestBitBoard(unittest.TestCase):
    def test_createFromFen(self):
        self.assert(BitBoard.createFromFen(), 0)
