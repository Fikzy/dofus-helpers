import sys

import app
import dofus_patcher
import exec_handler


def main(argv: list[str]):

    # Setup game handler
    handler = exec_handler.ExecHandler("Dofus 2.*")
    patcher = dofus_patcher.DofusPatcher(handler.get_pid())
    patcher.patch_autotravel()

    # Run app
    # app.run_app(argv, handler)


if __name__ == "__main__":
    main(sys.argv)
