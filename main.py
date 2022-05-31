import logging

import yaml

from chess_engine import ChessEngine


def create_logger(module_name: str, level: int | str = logging.INFO) -> logging.Logger:
    """
    Creates logger and returns an instance of logging object.
    :param level: The level for logging. (Default: logging.INFO)
    :param module_name: Logger name that will appear in text.
    :return: Logging Object.
    """
    # Setting up the root logger
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    log_stream = logging.FileHandler(filename="UCI_Communication.log")
    log_stream.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
    log_stream.setFormatter(formatter)
    logger.addHandler(log_stream)
    return logger


def initialize_uci_connection():
    """
    Initializes the connection between the chess engine and the GUI using Universal Chess Interface (UCI) Protocol.

    :return: None
    """
    assert input() == "uci", "The engine only supports UCI protocol"
    # print("Received <- uci")
    with open("engine_info.yaml") as fp:
        engine_configs = yaml.safe_load(fp)
        for key, value in engine_configs.items():
            if key == 'option name':
                for option in value:
                    print(f"option name {option}")
            elif not isinstance(value, list):
                print(f"{key} {value}")

    if set_options := engine_configs.get("setoption name"):
        for option in set_options:
            print(f"setoption name {option}")
    print("uciok")
    # while (uci_output := input()) != "isready":
    #     pass
    #     # print(f"Received <- {uci_output}")
    # print("readyok")


def main():
    initialize_uci_connection()
    if input() == "ucinewgame":
        engine = ChessEngine()
        engine.play()


if __name__ == '__main__':
    main()
