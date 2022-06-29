# Main marker
DofusClientMain
    AOB: F1 * * * F0 * * D0 30 57 2A D5 30 EF * * * * * * * 65 01 20 80 * 6D 05

# Autotravel
RoleplayWorldFrame: iftrue (11) -> iffalse (12)
    AOB: 11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * D0 66 * * 12 * * * F0
    Patch: 11 -> 12
    AOB: 11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * D0 66 * * 12 * * * EF
    Patch: 11 -> 12
    AOB: 11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * 26
    Patch: 11 -> 12

MountAutoTripManager: pushtrue (26) -> pushfalse (27)
    AOB: 26 61 * * 01 F0 * * D0 62 04
    Patch: 26 -> 27
    AOB: 26 61 * * 01 F0 * * D0 62 05
    Patch: 26 -> 27
    AOB: 26 61 * * 01 F0 * * D0 62 09
    Patch: 26 -> 27

CharacterDisplacementManager:
    # NOP out everything
    From: D0 30 20 80 * * 63 0C 20 80 * * 63 * 20 80 * * 63
    To: D0 D1 D2 D3 46 * * * * 80 * 63 0B


# Map tooltip
CartographyBase iffalse (12) -> iftrue (11)
    AOB: 12 * * * F0 * * D1 F0
    Patch: 12 -> 11
MapFlagMenuMaker: iffalse (12) -> jump (10)
    AOB: 12 * * * 29 62 07 82 76 2A 11
    Patch: 12 05 -> 10 0C
