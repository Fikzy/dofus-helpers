import logging

from patcher import FillNOPPatch, Patch, Patcher, ReplacementPatch

DOFUS_CLIENT_MAIN_MARKER = (
    "F1 * * * F0 * * D0 30 57 2A D5 30 EF * * * * * * * 65 01 20 80 * 6D 05"
)

PATCHES: list[Patch] = [
    # RoleplayWorldFrame
    ReplacementPatch(
        "11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * D0 66 * * 12 * * * F0",
        "12",
    ),
    ReplacementPatch(
        "11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * D0 66 * * 12 * * * EF",
        "12",
    ),
    ReplacementPatch("11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * 26", "12"),
    # MountAutoTripManager
    # - createNextMessage
    ReplacementPatch("26 61 * * 01 F0 * * D0 62 04", "27"),
    ReplacementPatch("26 61 * * 01 F0 * * D0 62 05", "27"),
    ReplacementPatch("26 61 * * 01 F0 * * D0 62 09", "27"),
    # - initNewTrip
    FillNOPPatch(
        "F0 * * D0 66 * * * 66 * * 80 * * D6 F0 * * D2 66 * * 96",
        "F0 * * D0 26 68 * * * F0 * * 60 * * D0 66 * * * 66 * * D0",
    ),
    # CartographyBase
    ReplacementPatch("12 * * * F0 * * D1 F0", "11"),
    # MapFlagMenuMaker
    ReplacementPatch("12 * * * 29 62 07 82 76 2A 11", "10 0C 00 00"),
    # CharacterDisplacementManager
    FillNOPPatch(
        "F1 * * * F0 * D0 30 20 80 * * 63 0C 20 80",
        "D0 D1 D2 D3 46 * * * * 80 * 63 0B",
    ),
]


class DofusPatcher(Patcher):
    def __init__(self):
        super().__init__("Dofus")

    def patch_autotravel(self) -> bool:

        # DofusClientMain
        _, p_begin, p_buffer = self.scan(DOFUS_CLIENT_MAIN_MARKER)

        if not p_begin:
            logging.error("Failed to find DofusClientMain marker point.")
            return False

        for patch in PATCHES:
            if not self.apply_patch(p_begin, p_buffer, patch):
                return False

        return True
