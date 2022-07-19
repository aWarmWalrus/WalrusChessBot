import bitboard
import copy
import sys
import random
import time
from bitboard import BitBoard
from collections import defaultdict
from threading import Thread

ENGINE_NAME = "BAD_MINIMAX"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "rn2k3/2pp1pp1/2b1pn2/1BB5/P3P3/1PN2Q1r/2PP1P1P/R3K1NR w KQq - 0 15"

PIECE_VALUES = {bitboard.PAWN: 100,
                bitboard.ROOK: 500,
                bitboard.BISHOP: 300,
                bitboard.KNIGHT: 400,
                bitboard.QUEEN: 900,
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
        info = {}
        info['score'] = -1000 if self._board.whiteToMove() else 1000
        info['moves'] = []
        searcher = Thread(target=self.search, args=(self._board,info,), daemon=True)
        searcher.start()
        searcher.join()
        if searcher.is_alive():
            print("TIMED OUT")
        # bestMove, score = self.search(self._board)
        if abs(info['score']) == 100:
            print("Forced check mate found!!")
        bestMoves = copy.copy(info['moves'])
        first = True
        while len(info['moves']) == 0:
            if first:
                print("haaaard time out")
                first = False
            pass
        print(bestMoves)
        print(info['score'])
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
            return -10000 if board.whiteToMove() else 10000
        whites, blacks = board.activePieces()
        whiteScore = sum([PIECE_VALUES[p] for p in whites])
        blackScore = sum([PIECE_VALUES[p] for p in blacks])
        return whiteScore - blackScore

    def search(self, board, info, depth = 0):
        if board.isCheckMate():
            return 1, (-10000 if board.whiteToMove() else 10000)
        if len(board.getLegalMoves()) == 0:  # stalemate
            return 1, 0
        if depth == self._maxDepth:
            score = MiniMaxEngine.evaluatePosition(board)
            return 1, score

        # best move for the active player.
        bestMoves = []
        bestScore = -10000 if board.whiteToMove() else 10000
        i = 0
        nodes = 0
        if depth == 0:
            start = time.time()
        for move in board.getLegalMoves():
            i += 1
            if depth == 0:
                print("info currmove {} currmovenumber {}".format(move, i))
            newBoard = board.makeMove(move)
            newNodes, score = self.search(newBoard, {}, depth + 1)
            nodes += newNodes
            if (board.whiteToMove() and (score > bestScore)) or \
                    ((not board.whiteToMove()) and (score < bestScore)):
                # print("better score: " + str(score))
                # newBoard.prettyPrint()
                if depth == 0:
                    print(str(depth) + ": move " + move + " score: " + str(score))
                    info['score'] = score
                    info['moves'] = [move]
                bestScore = score
                bestMoves = [move]
                continue
            if score == bestScore:
                # print("same score: " + str(score))
                # newBoard.prettyPrint()
                if depth == 0:
                    info['moves'].append(move)
                bestMoves.append(move)
        if depth == 0:
            elapsedMs = int((time.time() - start) * 1000)
            print("info depth {} score cp {} time {} nodes {} pv {}".format( \
                self._maxDepth, bestScore, elapsedMs, nodes, bestMoves[0]))
        # print(bestMoves)
        return nodes, bestScore


if __name__ == "__main__":
    engine = MiniMaxEngine()
    # engine._board = BitBoard.createFromFen(TEST_FEN)
    # engine.go()
    # print(sys.getsizeof(engine._board))
    #
    # print(engine.go())
    engine.run()
