import logging

import dofus_patcher

logging.basicConfig(level=logging.DEBUG)


def main():

    try:
        patcher = dofus_patcher.DofusPatcher()
    except Exception as e:
        exit(e)

    if not patcher.patch_autotravel():
        exit(
            "Failed to apply patch. Aborting.\n"
            "Make sure the game on the Authentication screen."
        )

    print("Successfuly patched autotravel!")


if __name__ == "__main__":
    main()
