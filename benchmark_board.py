import timeit
from arrayboard import Array2DBoard
from bitboard import BitBoard

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

def benchmark(board):
    moves50 = "h2h3 a7a6 e2e3 h7h5 d1e2 d7d6 e2h5 b7b6 h5d1 c8g4 f1d3 c7c5 f2f4 h8h5 h3g4 g7g5 e1f1 f8g7 h1h4 g7h8 f4g5 d8d7 g4h5 f7f5 h4h2 a8a7 d1g4 b8c6 c2c3 a7a8 d3c4 c6b4 c4e6 e8f8 d2d3 f8e8 e6f5 d7c6 g1f3 c6d5 g4f4 d5d4 f5h3 e7e6 b1d2 b4d5 h2h1 c5c4 f4f8 e8f8 f1g1 a6a5 a2a4 d5c3 g2g3 c4d3 h3f5 f8e7 f5h7 d4a4 g1f2 e7d8 h1f1 c3a2 b2b4 b6b5 f1e1 e6e5 f3d4 a4c2 e1f1 c2b3 g3g4 b3d5 h7e4 a5b4 e4h1 h8f6 d2b3 d8d7 h1d5 a8a5 f2g3 a2c1 g3h2 a5a8 f1h1 f6d8 h2g2 d8g5 h1e1 g5h6 a1a8 c1e2 d4e6 g8f6 a8a5 f6e8 e1d1".split()
    moves100 = "h2h3 a7a6 e2e3 h7h5 d1e2 d7d6 e2h5 b7b6 h5d1 c8g4 f1d3 c7c5 f2f4 h8h5 h3g4 g7g5 e1f1 f8g7 h1h4 g7h8 f4g5 d8d7 g4h5 f7f5 h4h2 a8a7 d1g4 b8c6 c2c3 a7a8 d3c4 c6b4 c4e6 e8f8 d2d3 f8e8 e6f5 d7c6 g1f3 c6d5 g4f4 d5d4 f5h3 e7e6 b1d2 b4d5 h2h1 c5c4 f4f8 e8f8 f1g1 a6a5 a2a4 d5c3 g2g3 c4d3 h3f5 f8e7 f5h7 d4a4 g1f2 e7d8 h1f1 c3a2 b2b4 b6b5 f1e1 e6e5 f3d4 a4c2 e1f1 c2b3 g3g4 b3d5 h7e4 a5b4 e4h1 h8f6 d2b3 d8d7 h1d5 a8a5 f2g3 a2c1 g3h2 a5a8 f1h1 f6d8 h2g2 d8g5 h1e1 g5h6 a1a8 c1e2 d4e6 g8f6 a8a5 f6e8 e1d1 d3d2 d1g1 e2c1 g2f1 d2d1n d5a8 e5e4 f1g2 d6d5 g1e1 d7c8 g2g1 h6f4 a8d5 c8b8 d5e4 d1e3 e1d1 f4c7 h5h6 c7a5 b3a1 e8d6 e4c6 e3f5 d1f1 c1d3 g4g5 f5d4 e6c7 d6e8 f1f3 d4c2 c6d7 c2e1 f3d3 e8d6 c7b5 e1c2 d3f3 d6b5 d7b5 a5d8 g1h1 d8a5 f3g3 c2d4 g3h3 b8c8 g5g6 a5b6 h3b3 d4c6 b3d3 c6e7 d3d2 c8c7 d2f2 e7c6 f2f8 b6e3 f8f3 e3g1 f3g3 g1c5 h1h2 c6d4 g3e3 d4f5 h6h7 c5e7 b5d3 f5d4 h7h8b e7g5 e3e8 d4c2 e8g8 b4b3 g8a8 c7b6 h8f6 g5d2 a8a3 b6c5 a3a6 b3b2 h2g3 c2a3 a6b6 b2b1r d3f5 b1b5 g3h2 b5b4 f6h4 c5d5 h2g3 b4b5 f5h3".split()

    def boardInitialization(boardType):
        board = boardType.createFromFen(STARTING_FEN)

    def startposMoves(moves, board):
        for move in moves:
            board = board.makeMove(move)
        return board

    def computeLegalMoves(board):
        board.getLegalMoves()

    test1 = timeit.timeit("boardInitialization(type(board))", globals=locals(), number=1000)
    test2 = timeit.timeit("startposMoves(moves50, board)", globals=locals(), number=1000)
    test3 = timeit.timeit("startposMoves(moves100, board)",globals=locals(), number=1000)

    MOVES_99 = "q2Q3r/n6R/kpB1N1K1/p1p1Bppp/1PN3P1/1n1pp1b1/P1PPPP1P/r5Rb w - - 0 1"
    board = type(board).createFromFen(MOVES_99)
    test4 = timeit.timeit("computeLegalMoves(board)",globals=locals(), number=1000)

    print(type(board))
    print("    boardInitialization: {:.3f}µs".format(test1 * 1000))
    print("    startposMoves(50):    {:.3f}ms".format(test2))
    print("    startposMoves(100):   {:.3f}ms".format(test3))
    print("    computeLegalMoves():  {:.3f}µs".format(test4 * 1000))
    print()


if __name__ == '__main__':
    arrayBoard = Array2DBoard.createFromFen(STARTING_FEN)
    bitBoard = BitBoard.createFromFen(STARTING_FEN)
    benchmark(arrayBoard)
    benchmark(bitBoard)
