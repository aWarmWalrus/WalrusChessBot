import bitboard
import copy
import sys
import random
import time
from bitboard import BitBoard
from collections import defaultdict
from threading import Thread
from openings import OpeningTree

ENGINE_NAME = "ALPHA_BETA"
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
TEST_FEN = "8/1b6/p5R1/1p1kp3/3npq2/Q7/PP5P/5rNK w - - 6 38"
ALIREZA = "books/lichess_alireza.alg"
DEBUG = False
USE_BOOK = True

POS_INF = 1000000000
NEG_INF = -1000000000
WHITE_MATE = 1000000
BLACK_MATE = -1000000

PIECE_VALUES = {bitboard.PAWN:   100,
                bitboard.KNIGHT: 320,
                bitboard.BISHOP: 330,
                bitboard.ROOK:   500,
                bitboard.QUEEN:  900,
                bitboard.KING:   20000}
PAWN_VALUES = [0,  0,  0,  0,  0,  0,  0,  0, \
              50, 50, 50, 50, 50, 50, 50, 50, \
              10, 10, 20, 30, 30, 20, 10, 10, \
               5,  5, 10, 25, 25, 10,  5,  5, \
               5,  0,  0, 20, 20,  0,  0,  5, \
               5, -5,-10,  0,  0,-10, -5,  5, \
               5, 10, 10,-20,-20, 10, 10,  5, \
               0,  0,  0,  0,  0,  0,  0,  0]
KNIGHT_VALUES = [-50,-40,-30,-30,-30,-30,-40,-50,
                -40,-20,  0,  0,  0,  0,-20,-40,
                -30,  0, 10, 15, 15, 10,  0,-30,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -30,  0, 15, 20, 20, 15,  0,-30,
                -30,  5, 10, 15, 15, 10,  5,-30,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -50,-40,-30,-30,-30,-30,-40,-50]
BISHOP_VALUES = [-20,-10,-10,-10,-10,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0,  5, 10, 10,  5,  0,-10,
                -10,  5,  5, 10, 10,  5,  5,-10,
                -10,  0, 10, 10, 10, 10,  0,-10,
                -10, 10, 10, 10, 10, 10, 10,-10,
                -10,  5,  0,  0,  0,  0,  5,-10,
                -20,-10,-20,-10,-10,-20,-10,-20]
ROOK_VALUES = [0,  0,  0,  0,  0,  0,  0,  0,
              5, 10, 10, 10, 10, 10, 10,  5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
             -5,  0,  0,  0,  0,  0,  0, -5,
              0,  0,  0, 10, 10,  0,  0,  0]
QUEEN_VALUES = [-20,-10,-10, -5, -5,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0,  5,  5,  5,  5,  0,-10,
                 -5,  0,  5,  5,  5,  5,  0, -5,
                  0,  0,  5,  5,  5,  5,  0, -5,
                -10,  5,  5,  5,  5,  5,  0,-10,
                -10,  0,  5,  0,  0,  0,  0,-10,
                -20,-10,-10, -5, -5,-10,-10,-20]
KING_VALUES = [-30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -20,-30,-30,-40,-40,-30,-30,-20,
                -10,-20,-20,-20,-20,-20,-20,-10,
                 20, 20,  0,  0,  0,  0, 20, 20,
                 20, 50, 10,  0,  0, 10, 50, 20]
KING_ENDGAME = [-50,-40,-30,-20,-20,-30,-40,-50,
                -30,-20,-10,  0,  0,-10,-20,-30,
                -30,-10, 20, 30, 30, 20,-10,-30,
                -30,-10, 30, 40, 40, 30,-10,-30,
                -30,-10, 30, 40, 40, 30,-10,-30,
                -30,-10, 20, 30, 30, 20,-10,-30,
                -30,-30,  0,  0,  0,  0,-30,-30,
                -50,-30,-30,-30,-30,-30,-30,-50]
PAWN_ENDGAME = [0,  0,  0,  0,  0,  0,  0,  0, \
             400,400,400,400,400,400,400,400, \
             200,200,200,200,200,200,200,200, \
             100,100,100,100,100,100,100,100, \
              50, 50, 50, 50, 50, 50, 50, 50, \
              10, 10, 10, 10, 10, 10, 10, 10, \
               0,  0,  0,  0,  0,  0,  0,  0, \
               0,  0,  0,  0,  0,  0,  0,  0]
EVAL_TABLES = {bitboard.PAWN:   PAWN_VALUES,
               bitboard.KNIGHT: KNIGHT_VALUES,
               bitboard.BISHOP: BISHOP_VALUES,
               bitboard.ROOK:   ROOK_VALUES,
               bitboard.QUEEN:  QUEEN_VALUES,
               bitboard.KING:   KING_VALUES}
ENDGAME_TABLE = {bitboard.PAWN: PAWN_ENDGAME,
               bitboard.KNIGHT: KNIGHT_VALUES,
               bitboard.BISHOP: BISHOP_VALUES,
               bitboard.ROOK:   ROOK_VALUES,
               bitboard.QUEEN:  QUEEN_VALUES,
               bitboard.KING:   KING_ENDGAME}

class AlphaBetaEngine:
    def __init__(self):
        self._options = defaultdict(str)
        self._board = BitBoard(0)
        self._maxDepth = 5 # in plies
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
                        self._bookMoves = self._bookMoves.getChild(move)
                        if DEBUG:
                            self.printBookMoves()
                    else:
                        self._bookMoves = None
        elif words[1] == "fen":
            self._bookMoves = None
            self._board = BitBoard.createFromFen(" ".join(words[2:7]))
        else:
            print("weird " + words.join())

    def go(self, args):
        if USE_BOOK:
            bookMove = self.consultBook()
            if bookMove is not None:
                print("bestmove " + bookMove)
                return

        # Time management
        self._maxDepth = 4
        if len(args) > 1:
            if args[1] == "infinite":
                self._maxDepth = 6
            elif args[1] == "wtime":
                whiteTime = int(args[2])
                blackTime = int(args[4])
                usTime = whiteTime if self._board.whiteToMove() else blackTime
                opTime = blackTime if self._board.whiteToMove() else whiteTime
                if usTime < 900000:
                    self._maxDepth = 4
                # elif usTime >= opTime * 1.5:
                #     self._maxDepth = 5

        self._bestMoves = []
        moves = self._board.getLegalMoves()
        if len(moves) < 5:
            print("< 5 moves: {}".format(moves))
            self._maxDepth += 1
        print("DEBUG: searching max depth " + str(self._maxDepth))

        if self._board.isCheckMate():
            print("CHECK MATED SON")
            return
        elif len(moves) == 0:
            print("stale mate...??")
            return
        info = {"move":"",
                "score":NEG_INF if self._board.whiteToMove() else POS_INF,
                "pv":""}
        # searcher = Thread(target = self.search, args = (self._board, info,), daemon=True)
        # searcher.start()
        nodes, bestPath, score = self.search(self._board, info)
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
                self.go(line.split())
            elif line.startswith("print"):
                self._board.prettyPrint()
                print(self._board.getLegalMoves())
                print(AlphaBetaEngine.evaluatePosition(self._board))
            elif line.startswith("end") or line.startswith("quit"):
                print("goodbye")
                break

    """ =============== Alpha Beta implementation ====================="""
    def consultBook(self):
        if self._bookMoves is not None and self._moves < 12:
            children = self._bookMoves.getChildren()
            values = [c.getCount() for c in children.values()]
            return random.choices(list(children.keys()), values)[0]
        return None

    def evaluatePosition(board):
        if board.isCheckMate():
            return BLACK_MATE if board.whiteToMove() else WHITE_MATE
        numMinors = 0
        whites, blacks = board.activePieces()
        isEndgame = (len(whites) + len(blacks)) < 14
        evalTable = ENDGAME_TABLE if isEndgame else EVAL_TABLES

        whiteScore = 0
        for piece, index in whites:
            whiteScore += PIECE_VALUES[piece]
            whiteScore += evalTable[piece][index]

        blackScore = 0
        for piece, index in blacks:
            # Eval tables are not symmetric. a8 is at index 0, and specified
            # from white's perspective. Need to correct the index for black.
            # a8 (0)  => a1 (56)
            # a1 (56) => a8 (0)
            # a4 (32) => a5 (24)
            # b8 (1)  => b1 (57)
            # b1 (57) => b1 (1)
            # b4 (33) => b5 (25)
            col = index % 8
            bi = 56 - (index - col) + col
            # print("{}, {} = {}".format(bin(piece), bi, EVAL_TABLES[piece][bi]))
            blackScore += PIECE_VALUES[piece]
            blackScore += evalTable[piece][bi]
        # print("WHITE: {}    BLACK: {}    total: {}".format(whiteScore, blackScore, whiteScore-blackScore))
        # whiteScore = sum([PIECE_VALUES[p] for piece, index in whites])
        # blackScore = sum([PIECE_VALUES[p] for p in blacks])
        return whiteScore - blackScore

    def search(self, board, info, alpha=NEG_INF, beta=POS_INF, depth=0):
        if board.isCheckMate():
            return 1, "", (BLACK_MATE if board.whiteToMove() else WHITE_MATE)
        if len(board.getLegalMoves()) == 0:  # stalemate
            return 1, "", 0
        if depth == self._maxDepth:
            score = AlphaBetaEngine.evaluatePosition(board)
            return 1, "", score

        legalMoves = board.getLegalMoves()
        # if len(legalMoves) == 1:
        #     return 1, legalMoves[0] + " " + bestPath, 0   # forced move
        # best move for the active player.
        bestMoves = []
        bestScore = NEG_INF if board.whiteToMove() else POS_INF
        nodes = 0
        if depth == 0:
            start = time.time()
        bestPath = ""
        i = 0
        for move in legalMoves:
            i += 1
            if depth == 0:
                print("info currmove {} currmovenumber {}".format(move, i), flush=True)

            newBoard = board.makeMove(move)
            # path = moves + move + " "
            newNodes, path, score = self.search(newBoard, info, \
                alpha, beta, depth + 1)
            nodes += newNodes

            if board.whiteToMove() and (score > bestScore):
                bestScore = score
                bestMoves = [move]
                alpha = score
                bestPath = path
                if DEBUG:
                    print("info depth {} score cp {} nodes {} pv {}".format( \
                        self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                        nodes, path), flush=True)
                if depth == 0:
                    elapsedMs = int((time.time() - start) * 1000)
                    print("info depth {} score cp {} time {} nodes {} pv {}".format( \
                        self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                        elapsedMs, nodes, move + " " + bestPath), flush=True)
                if depth == 0 and score == WHITE_MATE:
                    print("White checkmate is inevitable: {} {}".format(move, bestPath))
                    break
            elif (not board.whiteToMove()) and (score < bestScore):
                bestScore = score
                bestMoves = [move]
                beta = score
                bestPath = path
                if DEBUG:
                    print("info depth {} score cp {} nodes {} pv {}".format( \
                        self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                        nodes, path), flush=True)
                if depth == 0:
                    elapsedMs = int((time.time() - start) * 1000)
                    print("info depth {} score cp {} time {} nodes {} pv {}".format( \
                        self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                        elapsedMs, nodes, move + " " + bestPath), flush=True)
                if depth == 0 and score == BLACK_MATE:
                    print("Black checkmate is inevitable: {} {}".format(move, bestPath))
                    break
            if score == bestScore:
                bestMoves.append(move)
            if alpha > beta:
                if DEBUG:
                    print("{}({}): alpha {} > beta {}: pruning {} other branches".format(\
                        "WHITE" if board.whiteToMove() else "BLACK", \
                        depth, alpha, beta, len(legalMoves) - i))
                break

        bestMove = random.choice(bestMoves)
        bestPath = bestMove + " " + bestPath
        # if board.whiteToMove():
        #     if depth == self._maxDepth or bestScore == WHITE_MATE:
        #         print("hello {} {}".format(bestScore, bestPath))
        #         info['score'] = bestScore
        #         info['pv'] = bestPath
        # else:
        #     if depth == self._maxDepth or bestScore == BLACK_MATE:
        #         print("hello {} {}".format(bestScore, path))
        #         info['score'] = bestScore
        #         info['pv'] = bestPath

        if depth == 0:
            info['move'] = bestMove
            elapsedMs = int((time.time() - start) * 1000)
            print("info depth {} score cp {} time {} nodes {} pv {}".format( \
                self._maxDepth, bestScore * (1 if board.whiteToMove() else -1), \
                elapsedMs, nodes, bestPath), flush=True)
        return nodes, bestPath, bestScore


if __name__ == "__main__":
    engine = AlphaBetaEngine()
    engine.run()
    # engine.position("position startpos moves g1h3 d7d5 h3g5 h7h6 g5h7 h8h7 h1g1 e7e5 g1h1 g8f6 h1g1 b8c6 g1h1 f8b4 h1g1 c8e6 g1h1 f6e4 h1g1 d8h4 g1h1 b4c5 h1g1 e8d7 g1h1 g7g6 h1g1 b7b6 g1h1")
    # engine.go([])
    # AlphaBetaEngine.evaluatePosition(engine._board)
