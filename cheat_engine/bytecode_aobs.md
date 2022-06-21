# Autotravel
RoleplayWorldFrame:
    AOB: 11 10 00 00 F0 D1 02 60 D3 08 46 CF FE 02 00
    Patch: 11 -> 12
    AOB: 11 10 00 00 F0 F8 02 60 D3 08 46 CF FE 02 00
    Patch: 11 -> 12
    AOB: 11 10 00 00 F0 C7 09 60 D3 08 46 CF FE 02 00
    Patch: 11 -> 12

MountAutoTripManager:
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
MapFlagMenuMaker
    AOB: 12 05 00 00 29 62 07 82 76 2A 11
    Patch: 12 05 -> 10 0C
CartographyBase
    AOB: 12 40 00 00 F0 85 0C D1
    Patch: 12 -> 11

<!-- # Jump from first if to bottom, NO WORK
AOB: 12 04 00 00 29 62 05 96 12 42 00 00
Patch: 12 04 -> 10 9E

# Jump directly from function start to bottom, NO WORK
AOB: 20 80 96 05 63 0C 20 80 80 02
Patch: 20 80 96 05 -> 10 9E 00 00

# Invert last if to debug (should get no dest message)
AOB: 11 3F 00 00 F0 AE 01 60 AA 01
Patch: 11 -> 12

# Skip first if
AOB: 12 04 00 00 29 62 05 96 12 42 00 00
Patch: 12 04 -> 12 42 -->

<!-- # NOP out:
    From: 60 B3 8C 01 87 66 E6 87 01 11 10 00 00
    To: 02 D0 66 B3 39 12 D1 00 00 EF 01 9B E5 -->
