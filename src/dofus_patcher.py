import logging

from patcher import FillNOPPatch, Patch, Patcher, ReplacementPatch

DOFUS_CLIENT_MAIN_MARKER = "F1 FC 87 07 F0 9E"

PATCHES: list[Patch] = [
    # RoleplayWorldFrame
    ReplacementPatch("11 10 00 00 F0 D1", "12"),
    ReplacementPatch("11 10 00 00 F0 F8 02 60", "12"),
    ReplacementPatch("11 10 00 00 F0 C7 09", "12"),
    # MountAutoTripManager
    ReplacementPatch("26 61 E6 87 01 F0 CF", "27"),
    ReplacementPatch("26 61 E6 87 01 F0 DA", "27"),
    ReplacementPatch("26 61 E6 87 01 F0 90", "27"),
    # CartographyBase
    ReplacementPatch("12 40 00 00 F0 85 0C D1", "11"),
    # MapFlagMenuMaker
    ReplacementPatch("12 05 00 00 29 62 07 82 76 2A 11", "10 0C"),
    # CharacterDisplacementManager
    FillNOPPatch("F1 AA 8E 08 F0 52", "D0 D1 D2 D3 46 A0 BF 01 03 80 14 63 0B"),
]


class DofusPatcher(Patcher):
    def __init__(self):
        super().__init__("Dofus")

    def patch_autotravel(self) -> bool:

        # DofusClientMain
        _, p_begin, p_buffer = self.scan(
            DOFUS_CLIENT_MAIN_MARKER, exp_page_size=0x13E1000
        )

        if not p_begin:
            logging.error("Failed to find DofusClientMain marker point.")
            return False

        for patch in PATCHES:
            if not self.apply_patch(p_begin, p_buffer, patch):
                return False

        return True
