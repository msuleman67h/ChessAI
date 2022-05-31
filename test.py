from chess import Board

from game_state import GameState, PieceColor


def main():
    b = Board("r1bq1rk1/pp3pp1/2n2n1p/1p2p2P/3p4/1PPPQ3/P3PPP1/3RKBNR b K - 1 12")
    b.push_san("d4e3")
    print(b)

    gs = GameState(b, 0)
    gs.our_color = PieceColor.WHITE
    print(gs.evaluate())


if __name__ == '__main__':
    main()
