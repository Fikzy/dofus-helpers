import re


def str_to_bytearray(pattern: str | bytearray) -> bytearray:
    if isinstance(pattern, str):
        return bytearray.fromhex(pattern)
    return pattern


def convert_pattern(pattern: str) -> bytearray:
    """
    AOB pattern from string. Space separated. Use '*' or '?' as wild card.
    """
    bytes_str = pattern.replace("?", "*").split(" ")
    escaped_bytes = b"".join(
        [re.escape(bytearray.fromhex(b)) if b != "*" else b"." for b in bytes_str]
    )
    return escaped_bytes
