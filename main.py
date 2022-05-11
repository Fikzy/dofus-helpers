import os
import sys

import app
import exec_handler
import world_graph_parser


def main(argv: list[str]):

    handler = exec_handler.ExecHandler(title_regex=".* - Dofus.*")

    exec_path = handler.get_path()
    game_directory = os.path.dirname(exec_path)

    graph = world_graph_parser.WorlGraph(game_directory)
    print(len(graph.vertices))

    app.run_app(argv)


if __name__ == "__main__":
    main(sys.argv)
