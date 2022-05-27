import sys

import app
import dofus_handler


def main(argv: list[str]):

    # Setup game handler
    handler = dofus_handler.DofusHandler()

    # Run app
    app.run_app(argv, handler)


if __name__ == "__main__":
    main(sys.argv)
