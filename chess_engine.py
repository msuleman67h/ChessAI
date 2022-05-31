from multiprocessing import Process, Queue
from threading import Thread
from typing import Optional

from chess import Board

from game_state import GameState, PieceColor


class ChessEngine:
    def __init__(self):
        self.game_state: GameState = GameState(board=Board(), depth=1)
        self.white_time: int = 0
        self.black_time: int = 0
        self.quit_game: bool = False
        self.search_thread: Optional[Thread] = None
        self.search_process: Optional[Process] = None
        self.process_queue = Queue()

    def set_color(self, color: PieceColor):
        if self.game_state.our_color == PieceColor.UNKNOWN:
            self.game_state.our_color = color
            # print(f"AI color is {color}")

    def play(self):
        while not self.quit_game:
            self.process_input(input())

    def process_input(self, uci_input: str):
        if uci_input == "isready":
            print("readyok")
        elif uci_input == "ucinewgame":
            self.__init__()
        elif uci_input.startswith("position startpos moves"):
            self.set_color(PieceColor.BLACK)
            if self.search_process:
                self.game_state.board.push_uci(self.process_queue.get()[0])
                self.search_process.join()
            self.game_state.board.push_uci(uci_input.split()[-1])
        elif uci_input.startswith("position fen"):
            if self.search_process:
                self.game_state.board.push_uci(self.process_queue.get()[0])
                self.search_process.join()
            if "moves" in uci_input:
                self.set_color(PieceColor.BLACK)
                self.game_state.board.push_uci(uci_input.split()[-1])
            else:
                self.game_state.board.set_board_fen(" ".join(uci_input.split()[2:3]))
        elif uci_input.startswith("go"):
            self.set_color(PieceColor.WHITE)
            self.game_state.stop_search = False
            # self.game_state.find_best_move(self.process_queue)
            # self.search_thread = Thread(target=self.game_state.find_best_move)
            # self.search_thread.start()
            self.search_process = Process(target=self.game_state.find_best_move, args=(self.process_queue,))
            self.search_process.start()

        elif uci_input == "stop":
            self.game_state.stop_search = True
            print(f"bestmove {self.game_state.best_move}")
        elif uci_input == 'quit':
            self.quit_game = True
            if self.search_process:
                self.search_process.terminate()
        else:
            pass
            # print(f"Received <- {uci_input}")
