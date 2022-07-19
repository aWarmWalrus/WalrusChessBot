import copy
import sys
import random
import bitboard
from bitboard import BitBoard
from collections import defaultdict
from threading import Thread

ENGINE_NAME = "BAD_MINIMAX"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "rn2k3/2pp1pp1/2b1pn2/1BB5/P3P3/1PN2Q1r/2PP1P1P/R3K1NR w KQq - 0 15"

PIECE_VALUES = {bitboard.PAWN: 1,
                bitboard.ROOK: 5,
                bitboard.BISHOP: 3,
                bitboard.KNIGHT: 4,
                bitboard.QUEEN: 9,
                bitboard.KING: 100000}

class MiniMaxEngine:
    def __init__(self):
        self._options = defaultdict(str)
        self._board = BitBoard(0)
        self._maxDepth = 3 # in plies
        self._table = {}

    def inputUCI(self):
        print("id name " + ENGINE_NAME)
        print("id author Walrus")
        print("uciok")

    def setOptions(self, line):
        print("unimplemented")

    def isReady(self):
        print("readyok")

    def newGame(self):
        self._table = {}

    def position(self, line):
        words = line.split()
        assert(words[0] == "position")

        if words[1] == "startpos":
            self._board = BitBoard.createFromFen(STARTING_FEN)
            if len(words) > 2 and words[2] == "moves":
                for move in words[3:]:
                    self._board = self._board.makeMove(move)
        else:
            print("weird " + words.join())

    def go(self):
        self._bestMoves = []
        moves = self._board.getLegalMoves()
        if self._board.isCheckMate():
            print("CHECK MATED SON")
            return
        elif len(moves) == 0:
            print("stale mate...??")
            return
        bests = {}
        bests['score'] = -1000 if self._board.whiteToMove() else 1000
        bests['moves'] = []
        searcher = Thread(target=self.search, args=(self._board,bests,), daemon=True)
        searcher.start()
        searcher.join()
        if searcher.is_alive():
            print("TIMED OUT")
        # bestMove, score = self.search(self._board)
        if abs(bests['score']) == 100:
            print("Forced check mate found!!")
        # Getting a "list index out of range" error here sometimes..
        bestMoves = copy.copy(bests['moves'])
        first = True
        while len(bests['moves']) == 0:
            if first:
                print("haaaard time out")
                first = False
            pass
        print(bestMoves)
        print(bests['score'])
        print("bestmove " + random.choice(bestMoves))

    def run(self):
        while True:
            line = input()
            if line == "uci":
                self.inputUCI()
            elif line.startswith("setoption"):
                self.setOptions(line)
            elif line.startswith("isready"):
                self.isReady()
            elif line.startswith("ucinewgame"):
                self.newGame()
            elif line.startswith("position"):
                self.position(line)
            elif line.startswith("go"):
                self.go()
            elif line.startswith("print"):
                self._board.prettyPrint()
                print(self._board.getLegalMoves())
            elif line.startswith("end") or line.startswith("quit"):
                print("goodbye")
                break

    """ =============== Minimax implementation ====================="""
    def evaluatePosition(board):
        if board.isCheckMate():
            return -100 if board.whiteToMove() else 100
        whites, blacks = board.activePieces()
        whiteScore = sum([PIECE_VALUES[p] for p in whites])
        blackScore = sum([PIECE_VALUES[p] for p in blacks])
        return whiteScore - blackScore

    def search(self, board, bests, depth = 0):
        if board.isCheckMate():
            return "", (-100 if board.whiteToMove() else 100)
        if len(board.getLegalMoves()) == 0:  # stalemate
            return "", 0
        if depth == self._maxDepth:
            score = MiniMaxEngine.evaluatePosition(board)
            return "", score

        # best move for the active player.
        bestMoves = []
        bestScore = -1000 if board.whiteToMove() else 1000
        for move in board.getLegalMoves():
            newBoard = board.makeMove(move)
            _, score = self.search(newBoard, {}, depth + 1)
            if (board.whiteToMove() and (score > bestScore)) or \
                    ((not board.whiteToMove()) and (score < bestScore)):
                # print("better score: " + str(score))
                # newBoard.prettyPrint()
                if depth == 0:
                    print(str(depth) + ": move " + move + " score: " + str(score))
                    bests['score'] = score
                    bests['moves'] = [move]
                bestScore = score
                bestMoves = [move]
                continue
            if score == bestScore:
                # print("same score: " + str(score))
                # newBoard.prettyPrint()
                if depth == 0:
                    bests['moves'].append(move)
                bestMoves.append(move)
        # print(bestMoves)
        return _, bestScore


if __name__ == "__main__":
    engine = MiniMaxEngine()
    # engine._board = BitBoard.createFromFen(TEST_FEN)
    # engine.go()
    # print(sys.getsizeof(engine._board))
    #
    # print(engine.go())
    engine.run()
