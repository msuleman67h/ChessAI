"""
Filename: game__state.py
Author: Muhammad Suleman
Date: 2022/05/25
"""
from contextlib import suppress
from enum import Enum
from itertools import islice
from multiprocessing import Queue
from random import choice, shuffle
from sys import stdout

import chess
import numpy as np
from chess import Board

# import numpy as np

# Positional Values for all chess pieces
#                           a1, b1, c1, d1, e1, f1, g1, h1

pawn_positional_value = [0, 0, 0, 0, 0, 0, 0, 0,
                         1, 1, 1, 1, 1, 1, 1, 1,
                         1, 1, 1, 1, 1, 1, 1, 1,
                         2, 2, 2, 2, 2, 2, 2, 2,
                         2, 2, 2, 2, 2, 2, 2, 2,
                         4, 4, 4, 4, 4, 4, 4, 4,
                         5, 5, 5, 5, 5, 5, 5, 5,
                         8, 8, 8, 8, 8, 8, 8, 8]


class PieceColor(Enum):
    BLACK = 0
    WHITE = 1
    UNKNOWN = 2


class ChessPieces(Enum):
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = range(1, 7)


class GameState:
    CHECKMATE: int = 99999
    pieces_weight: dict[ChessPieces, int] = {ChessPieces.PAWN: 1,
                                             ChessPieces.KNIGHT: 4,
                                             ChessPieces.BISHOP: 4,
                                             ChessPieces.ROOK: 8,
                                             ChessPieces.QUEEN: 20,
                                             ChessPieces.KING: 1000
                                             }
    stop_search: bool = False
    max_lookup_depth: int = 5
    best_move: str = "0000"
    our_color: PieceColor = PieceColor.UNKNOWN

    def __init__(self, board: Board, depth: int):
        self.board: Board = board
        self.curr_depth: int = depth

    def find_random_legal_move(self):
        GameState.best_move = choice(list(self.board.generate_legal_moves())).uci()
        self.board.push_uci(GameState.best_move)
        if not GameState.stop_search:
            stdout.write(f"bestmove {GameState.best_move}")
            stdout.flush()

    def find_best_move(self, process_queue: Queue):
        GameState.nodes_searched = 0
        try:
            self._minimax(alpha=-GameState.CHECKMATE, beta=GameState.CHECKMATE)
        except InterruptedError:
            print("stopped early")
        if not GameState.stop_search:
            process_queue.put([self.best_move])
            stdout.write(f"bestmove {self.best_move}\n")
            stdout.flush()

    def _minimax(self, alpha: int, beta: int):
        if GameState.stop_search:
            raise InterruptedError

        if self.curr_depth == GameState.max_lookup_depth:
            return self.evaluate()

        if self.board.turn == PieceColor.WHITE.value:
            max_score = -GameState.CHECKMATE
            for legal_move in self.get_valid_moves():
                self.board.push(legal_move)
                self.curr_depth += 1
                score = self._minimax(alpha=alpha, beta=beta)
                if score >= max_score:
                    max_score = score
                    if self.curr_depth == 2:
                        GameState.best_move = legal_move.uci()
                self.board.pop()
                self.curr_depth -= 1
                alpha = max(alpha, max_score)
                if max_score >= beta:
                    break
            return max_score
        else:
            min_score = GameState.CHECKMATE
            for legal_move in self.get_valid_moves():
                self.board.push(legal_move)
                self.curr_depth += 1
                score = self._minimax(alpha=alpha, beta=beta)
                if score <= min_score:
                    min_score = score
                    if self.curr_depth == 2:
                        GameState.best_move = legal_move.uci()
                self.board.pop()
                self.curr_depth -= 1
                beta = min(beta, min_score)
                if min_score <= alpha:
                    break
            return min_score

    def is_piece_alive(self, chess_piece: ChessPieces, piece_color: PieceColor) -> bool:
        alive_pieces = [(pieces.piece_type, pieces.color) for (_, pieces) in self.board.piece_map().items()]
        if (chess_piece.value, piece_color.value) in alive_pieces:
            return True
        else:
            return False

    def is_defended(self, chess_square: int) -> bool:
        """
        Checks if the piece on the square belongs to us and is under attack by us.

        :param chess_square: Index of chess square.
        :return: True if the pieces is defended else False.
        """
        piece: chess.Piece = self.board.piece_at(chess_square)
        with suppress(AttributeError):
            if piece.color == self.our_color.value:
                return self.board.is_attacked_by(self.our_color.value, chess_square)
        return False

    def evaluate(self):
        # Adds for checkmate
        if self.board.is_checkmate():
            if self.board.turn == PieceColor.WHITE.value:
                return -GameState.CHECKMATE
            else:
                return GameState.CHECKMATE

        # To make the bot pick check moves
        score = 0
        if self.board.is_check():
            # White is being checked
            if self.board.turn == PieceColor.WHITE.value:
                # go through all the pieces that are checking king
                for checker_square_index in self.board.checkers():
                    # If our piece is being defended by a pieces than check has value
                    if self.is_defended(checker_square_index):
                        score -= 3
                    else:
                        score += 3
            # Black is being checked
            else:
                for checker_square_index in self.board.checkers():
                    if self.is_defended(checker_square_index):
                        score += 3
                    else:
                        score -= 3

        # Our Queen Dies but not theirs
        if not self.is_piece_alive(ChessPieces.QUEEN, PieceColor.WHITE) and self.is_piece_alive(ChessPieces.QUEEN, PieceColor.BLACK):
            score -= 50
        elif not self.is_piece_alive(ChessPieces.QUEEN, PieceColor.BLACK) and self.is_piece_alive(ChessPieces.QUEEN, PieceColor.WHITE):
            score += 50

        # To make the bot pick castling
        last_move: chess.Move = self.board.peek()
        last_move_piece: chess.Piece = self.board.piece_at(last_move.to_square)
        if self.board.is_castling(last_move):
            if self.our_color.value == last_move_piece.color:
                if self.our_color == PieceColor.WHITE:
                    score += 3
                elif self.our_color == PieceColor.BLACK:
                    score -= 3

        if self.board.turn == PieceColor.WHITE.value:
            score += len(list(self.board.generate_legal_moves())) * 0.001
        else:
            score -= len(list(self.board.generate_legal_moves())) * 0.001

        # position evaluation
        # Not really sure why TypeError is thrown occasionally. Could be a bug from library.
        with suppress(TypeError):
            for position, piece in self.board.piece_map().items():
                piece_type: ChessPieces = ChessPieces(piece.piece_type)
                piece_color: PieceColor = PieceColor(piece.color)

                if piece_type == ChessPieces.PAWN:
                    if piece_color == PieceColor.WHITE and self.our_color == PieceColor.WHITE:
                        score += pawn_positional_value[position] * 0.1
                    elif self.our_color == PieceColor.BLACK:
                        score -= np.flip(np.array(pawn_positional_value))[position] * 0.1
                if self.is_defended(position):
                    if self.our_color == PieceColor.WHITE:
                        score += 5
                    else:
                        score -= 5

        # material evaluation
        for color in islice(PieceColor, 2):
            for chess_piece in ChessPieces:
                number_of_pieces = len(self.board.pieces(piece_type=chess_piece.value, color=color.value))
                if color == PieceColor.WHITE:
                    score += number_of_pieces * GameState.pieces_weight.get(chess_piece)
                else:
                    score -= number_of_pieces * GameState.pieces_weight.get(chess_piece)
        return score

    def print_board(self):
        print(self.board)

    def get_valid_moves(self) -> list[chess.Move]:
        legal_moves = [legal_move for legal_move in self.board.generate_legal_moves()]
        shuffle(legal_moves)
        return legal_moves
