import bitboard
import copy
import sys
import random
import time
from bitboard import BitBoard
from collections import defaultdict
from threading import Thread

ENGINE_NAME = "ALPHA_BETA"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "rn2k3/2pp1pp1/2b1pn2/1BB5/P3P3/1PN2Q1r/2PP1P1P/R3K1NR w KQq - 0 15"
ALIREZA = "books/lichess_alireza.alg"
DEBUG = False

PIECE_VALUES = {bitboard.PAWN: 100,
                bitboard.ROOK: 500,
                bitboard.BISHOP: 300,
                bitboard.KNIGHT: 400,
                bitboard.QUEEN: 900,
                bitboard.KING: 100000}

class AlphaBetaEngine:
    def __init__(self):
        self._options = defaultdict(str)
        self._board = BitBoard(0)
        self._maxDepth = 3 # in plies
        self._table = {}
        self._moves = 0
        try:
            self._openings = OpeningTree.generateFromFile(ALIREZA)
        except FileNotFoundError:
            self._openings = OpeningTree.generateFromFile("../" + ALIREZA)

    def inputUCI(self):
        print("id name " + ENGINE_NAME)
        print("id author Walrus")
        print("uciok")

    def setOptions(self, line):
        print("unimplemented")

    def isReady(self):
        print("readyok")

    def newGame(self):
        # _bookMoves is a OpeningsTree node that is not None as long as there
        # are still moves remaining.
        self._bookMoves = self._openings
        self._table = {}
        self._moves = 0

    def printBookMoves(self):
        print("book moves (moves #{})".format(self._moves))
        children = self._bookMoves.getChildren()
        for c in children:
            print("  {}: {}".format(c, children[c].getCount()))

    def position(self, line):
        words = line.split()
        assert(words[0] == "position")

        if words[1] == "startpos":
            self._bookMoves = self._openings
            self._moves = 0
            self._board = BitBoard.createFromFen(STARTING_FEN)
            if DEBUG:
                self.printBookMoves()
            if len(words) > 2 and words[2] == "moves":
                for move in words[3:]:
                    self._board = self._board.makeMove(move)
                    self._moves += 1
                    if self._bookMoves is None:
                        continue
                    if move in self._bookMoves.getChildren():
                        self._bookMoves = self._bookmoves.getChild(move)
                        if DEBUG:
                            self.printBookMoves()
                    else:
                        self._bookMoves = None
        else:
            print("weird " + words.join())

    def go(self):

        bookMove = self.consultBook()
        if bookMove is not None:
            print("bestmove " + bookMove)
            return

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
        info['move'] = ""
        nodes, score = self.search(self._board, info)
        # print(bestMoves)
        # print(info['score'])
        print("bestmove " + info['move'])

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

    """ =============== Alpha Beta implementation ====================="""
    def consultBook(self):
        if self._bookMoves is not None:
            children = self._bookMoves.getChildren()
            values = [c.getCount() for c in children.values()]
            return random.choices(list(children.keys()), values)[0]
        return None

    def evaluatePosition(board):
        if board.isCheckMate():
            return -10000 if board.whiteToMove() else 10000
        whites, blacks = board.activePieces()
        whiteScore = sum([PIECE_VALUES[p] for p in whites])
        blackScore = sum([PIECE_VALUES[p] for p in blacks])
        return whiteScore - blackScore

    def search(self, board, info, alpha = -1000000, beta = 1000000, depth = 0):
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
            newNodes, score = self.search(newBoard, {}, alpha, beta, depth + 1)
            nodes += newNodes

            if (board.whiteToMove() and (score > bestScore)) or \
                    ((not board.whiteToMove()) and (score < bestScore)):
                if depth == 0:
                    print(str(depth) + ": move " + move + " score: " + str(score))
                    info['score'] = score
                    info['moves'] = [move]
                bestScore = score
                bestMoves = [move]
                continue
            if score == bestScore:
                if depth == 0:
                    info['moves'].append(move)
                bestMoves.append(move)
        if depth == 0:
            elapsedMs = int((time.time() - start) * 1000)
            print("info depth {} score cp {} time {} nodes {} pv {}".format( \
                self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                elapsedMs, nodes, bestMoves[0]))
        return nodes, bestScore


if __name__ == "__main__":
    engine = AlphaBetaEngine()
    engine.run()
