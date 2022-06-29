import logging
import re

from memory import ReadWriteMemory
from utils import convert_pattern, str_to_bytearray


class Patch:
    pass


class ReplacementPatch(Patch):
    pattern: bytearray
    replacement: bytearray

    def __init__(self, pattern: str, replacement: str):
        self.pattern = convert_pattern(pattern)
        self.replacement = str_to_bytearray(replacement)

    def __str__(self) -> str:
        return f"{self.pattern.hex(sep=' ').upper()} | {self.replacement.hex(sep=' ').upper()}"


class FillNOPPatch(Patch):
    start_pattern: bytearray
    end_pattern: bytearray

    def __init__(self, start_pattern: str, end_pattern: str):
        self.start_pattern = convert_pattern(start_pattern)
        self.end_pattern = convert_pattern(end_pattern)

    def __str__(self) -> str:
        return f"{self.start_pattern.hex(sep=' ').upper()} {self.end_pattern.hex(sep=' ').upper()}"


class Patcher(ReadWriteMemory):
    def find_pattern(
        self,
        page_begin: int,
        page_buffer: bytearray,
        pattern: bytearray,
    ):
        match = re.search(bytes(pattern), page_buffer)

        if not match:
            return None

        return page_begin + match.span()[0]

    def apply_replacement_patch(
        self,
        page_begin: int,
        page_buffer: bytearray,
        patch: ReplacementPatch,
    ):

        ptr = self.find_pattern(page_begin, page_buffer, patch.pattern)

        if not ptr or not self.write(ptr, patch.replacement):
            logging.debug(f"Failed to apply replacement patch: {patch}")
            return False

        return True

    def apply_fill_nop_patch(
        self,
        page_begin: int,
        page_buffer: bytearray,
        patch: FillNOPPatch,
    ):

        start_ptr = self.find_pattern(page_begin, page_buffer, patch.start_pattern)
        end_ptr = self.find_pattern(page_begin, page_buffer, patch.end_pattern)

        if not end_ptr or not self.fill(start_ptr, end_ptr, 0x02):
            logging.debug(f"Failed to apply fill nop patch: {patch}")
            return False

        return True

    def apply_patch(self, page_begin: int, page_buffer: bytearray, patch: Patch):

        if isinstance(patch, ReplacementPatch):
            return self.apply_replacement_patch(page_begin, page_buffer, patch)

        elif isinstance(patch, FillNOPPatch):
            return self.apply_fill_nop_patch(page_begin, page_buffer, patch)

        return False
