import argparse
import ctypes
import logging
import sys

import dofus_patcher


def popup(text: str, style: int = 0):
    return ctypes.windll.user32.MessageBoxW(0, text, "Dofus Helper", style)


def main(debug=False):

    if debug:
        logging.basicConfig(level=logging.DEBUG)

    try:
        patcher = dofus_patcher.DofusPatcher()
    except Exception as e:
        if not debug:
            popup(
                "Unable to find the game process.\n"
                "Make sure the game is open and on the authentication screen."
            )
        else:
            print(e)
        sys.exit()

    if not patcher.apply():
        if not debug:
            popup(
                "Failed to apply patch.\n"
                "The patch may already be applied.\n"
                "Otherwise, make sure the game is on the authentication screen."
            )
        sys.exit()

    if debug:
        print("Success!")
    else:
        popup("Successfully patched!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="show debug info")
    args = parser.parse_args()
    main(debug=args.debug)
