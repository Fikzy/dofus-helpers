from memory import *


class DofusPatcher(ReadWriteMemory):
    def __init__(self):
        super().__init__("Dofus")

    def find_pattern(
        self,
        page_begin: int,
        page_buffer: bytearray,
        pattern: str | bytearray,
    ):
        pattern = convert_pattern(pattern)

        offset = page_buffer.find(pattern)

        if offset == -1:
            print("Failed to find pattern in given buffer.")
            return None

        return page_begin + offset

    def patch(
        self,
        page_begin: int,
        page_buffer: bytearray,
        pattern: str | bytearray,
        patch: str | bytearray,
    ):

        pattern = convert_pattern(pattern)
        patch = convert_pattern(patch)

        ptr = self.find_pattern(page_begin, page_buffer, pattern)

        if not ptr or not self.write(ptr, patch):
            exit("Failed to apply patch. Aborting.")

    def fill_nop_patch(
        self,
        page_begin: int,
        page_buffer: bytearray,
        start_pattern: str | bytearray,
        end_pattern: str | bytearray,
    ):

        start_pattern = convert_pattern(start_pattern)
        end_pattern = convert_pattern(end_pattern)

        start_ptr = self.find_pattern(page_begin, page_buffer, start_pattern)
        end_ptr = self.find_pattern(page_begin, page_buffer, end_pattern)

        if not end_ptr or not self.fill(start_ptr, end_ptr, 0x02):
            exit("Failed to apply patch. Aborting.")

    def patch_autotravel(self) -> int:

        # DofusClientMain
        _, p_begin, p_buffer = self.scan("F1 FC 87 07 F0 9E", exp_page_size=0x13E1000)

        if not p_begin:
            print("Failed to find DofusClientMain marker point.")
            return

        print("DofusClientMain marker found")

        # RoleplayWorldFrame
        # iftrue (11) -> iffalse (12)
        self.patch(p_begin, p_buffer, "11 10 00 00 F0 D1", "12")
        self.patch(p_begin, p_buffer, "11 10 00 00 F0 F8 02 60", "12")
        self.patch(p_begin, p_buffer, "11 10 00 00 F0 C7 09", "12")
        print("RoleplayWorldFrame patch done")

        # MountAutoTripManager
        # pushtrue (26) -> pushfalse (27)
        self.patch(p_begin, p_buffer, "26 61 E6 87 01 F0 CF", "27")
        self.patch(p_begin, p_buffer, "26 61 E6 87 01 F0 DA", "27")
        self.patch(p_begin, p_buffer, "26 61 E6 87 01 F0 90", "27")
        print("MountAutoTripManager patch done")

        # CharacterDisplacementManager
        self.fill_nop_patch(
            p_begin,
            p_buffer,
            "F1 AA 8E 08 F0 52",
            "D0 D1 D2 D3 46 A0 BF 01 03 80 14 63 0B",
        )
        print("CharacterDisplacementManager patch done")
