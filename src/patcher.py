import logging
import re

from memory import ReadWriteMemory
from utils import convert_pattern, str_to_bytearray


def pattern_str(pattern: bytearray):
    return pattern.hex(sep=" ").upper()


def offset_str(offset: int):
    if not offset:
        return ""
    sign = "+" if offset > 0 else "-"
    return f" ({sign}{offset})"


class Patch:
    pass


class ReplacementPatch(Patch):
    pattern: bytearray
    offset: int
    replacement: bytearray

    def __init__(self, pattern: str, replacement: str, offset: int = 0):
        self.pattern = convert_pattern(pattern)
        self.offset = offset
        self.replacement = str_to_bytearray(replacement)

    def __str__(self) -> str:
        return f"ReplacementPatch: {pattern_str(self.pattern)}{offset_str(self.offset)} | {pattern_str(self.replacement)}"


class FillNOPPatch(Patch):
    start_pattern: bytearray
    start_offset: int
    end_pattern: bytearray
    end_offset: int

    def __init__(
        self,
        start_pattern: str,
        end_pattern: str,
        start_offset: int = 0,
        end_offset: int = 0,
    ):
        self.start_pattern = convert_pattern(start_pattern)
        self.start_offset = start_offset
        self.end_pattern = convert_pattern(end_pattern)
        self.end_offset = end_offset

    def __str__(self) -> str:
        return f"FillNOPPatch: {pattern_str(self.start_pattern)}{offset_str(self.start_offset)} => {pattern_str(self.end_pattern)}{offset_str(self.end_offset)}"


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

        if not ptr or not self.write(ptr + patch.offset, patch.replacement):
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

        if not end_ptr or not self.fill(
            start_ptr + patch.start_offset, end_ptr + patch.end_offset, 0x02
        ):
            logging.debug(f"Failed to apply fill nop patch: {patch}")
            return False

        return True

    def apply_patch(self, page_begin: int, page_buffer: bytearray, patch: Patch):

        if isinstance(patch, ReplacementPatch):
            return self.apply_replacement_patch(page_begin, page_buffer, patch)

        elif isinstance(patch, FillNOPPatch):
            return self.apply_fill_nop_patch(page_begin, page_buffer, patch)

        return False
