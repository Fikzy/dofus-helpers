# Autotravel
RoleplayWorldFrame: iftrue (11) -> iffalse (12)
    AOB: 11 10 00 00 F0 D1 02 60 D3 08 46 CF FE 02 00
    Patch: 11 -> 12
    AOB: 11 10 00 00 F0 F8 02 60 D3 08 46 CF FE 02 00
    Patch: 11 -> 12
    AOB: 11 10 00 00 F0 C7 09 60 D3 08 46 CF FE 02 00
    Patch: 11 -> 12

MountAutoTripManager: pushtrue (26) -> pushfalse (27)
    AOB: 26 61 E6 87 01 F0 CF 03
    Patch: 26 -> 27
    AOB: 26 61 E6 87 01 F0 DA 03
    Patch: 26 -> 27
    AOB: 26 61 E6 87 01 F0 90 04
    Patch: 26 -> 27

CharacterDisplacementManager:
    # NOP out everything
    From: F1 AA 8E 08 F0 52 D0 30 20 80 96 05 63
    To: 01 D0 D1 D2 D3 46 A0 BF 01 03 80 14 63 0B F0 AC 01


# Map tooltip
CartographyBase iffalse (12) -> iftrue (11)
    AOB: 12 40 00 00 F0 85 0C D1
    Patch: 12 -> 11
MapFlagMenuMaker: iffalse (12) -> jump (10)
    AOB: 12 05 00 00 29 62 07 82 76 2A 11
    Patch: 12 05 -> 10 0C
