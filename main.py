import os
import sys
from time import sleep

import app
import dofus_handler
import world_graph_parser


def main(argv: list[str]):

    # Setup game handler
    handler = dofus_handler.DofusHandler()

    while True:
        if handler.is_maximized():
            handler.draw_rect(handler.get_game_bounds(), (255, 0, 0))
            handler.draw_rect(handler.get_move_zones(), (0, 0, 255))
        sleep(0.05)

    # Load game data
    # exec_path = handler.get_path()
    # game_directory = os.path.dirname(exec_path)

    # graph = world_graph_parser.WorlGraph(game_directory)
    # print(len(graph.vertices))

    # Run app
    # app.run_app(argv)


if __name__ == "__main__":
    main(sys.argv)
