import argparse
import logging

import dofus_patcher


def main(debug=False):

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        patcher = dofus_patcher.DofusPatcher()
    except Exception as e:
        exit(e)

    if not patcher.patch_autotravel():
        exit(
            "Failed to apply patch. Aborting.\n"
            "Make sure the game is on the Authentication screen."
        )

    print("Successfuly patched autotravel!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="show debug info")
    args = parser.parse_args()
    main(debug=args.debug)
