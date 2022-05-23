import os
import sys
from time import sleep

import app
import dofus_handler
import world_graph_parser


def main(argv: list[str]):

    # Setup game handler
    handler = dofus_handler.DofusHandler()

    # Load game data
    # exec_path = handler.get_path()
    # game_directory = os.path.dirname(exec_path)

    # graph = world_graph_parser.WorlGraph(game_directory)
    # print(len(graph.vertices))

    # Run app
    app.run_app(argv, handler)


if __name__ == "__main__":
    main(sys.argv)
