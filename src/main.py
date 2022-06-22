import dofus_patcher


def main():

    try:
        patcher = dofus_patcher.DofusPatcher()
    except Exception as e:
        print(e)
        print("Make sure the game is open and on the Authentication screen.")
        return

    patcher.patch_autotravel()


if __name__ == "__main__":
    main()
