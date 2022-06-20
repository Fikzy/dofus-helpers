import sys

import app
import dofus_scanner
import exec_handler


def main(argv: list[str]):

    # Setup game handler
    handler = exec_handler.ExecHandler("Dofus 2.*")
    scanner = dofus_scanner.DofusScanner(handler.get_pid())
    scanner.patch_autotravel()

    # Run app
    # app.run_app(argv, handler)


if __name__ == "__main__":
    main(sys.argv)
