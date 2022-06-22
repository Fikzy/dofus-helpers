import atexit
import ctypes
import struct
import sys
import time
from ctypes import *
from ctypes.wintypes import *

import read_write_memory

k32 = WinDLL("kernel32", use_last_error=True)
psapi = WinDLL("psapi")

INVALID_HANDLE_VALUE = ctypes.c_ulonglong(-1).value
TH32CS_SNAPHEAPLIST = 0x00000001
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
MEM_FREE = 0x10000

PAGE_NOACCESS = 0x01
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE = 0x10
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_WRITECOPY = 0x80


class MODULEENTRY32(Structure):
    _fields_ = [
        ("dwSize", DWORD),
        ("th32ModuleID", DWORD),
        ("th32ProcessID", DWORD),
        ("GlblcntUsage", DWORD),
        ("ProccntUsage", DWORD),
        ("modBaseAddr", PBYTE),
        ("modBaseSize", DWORD),
        ("hModule", HMODULE),
        ("szModule", CHAR * 256),
        ("szExePath", CHAR * 260),
    ]


class MEMORY_BASIC_INFORMATION(Structure):
    _fields_ = [
        ("BaseAddress", LPVOID),
        ("AllocationBase", LPVOID),
        ("AllocationProtect", DWORD),
        ("PartitionId", WORD),
        ("RegionSize", c_size_t),
        ("State", DWORD),
        ("Protect", DWORD),
        ("Type", DWORD),
    ]


## CloseHandle
CloseHandle = k32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL

## ReadProcessMemory
ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = [HANDLE, LPCVOID, LPVOID, c_size_t, POINTER(c_size_t)]
ReadProcessMemory.restype = BOOL

## VirtualAllocEx
VirtualAllocEx = k32.VirtualAllocEx
VirtualAllocEx.argtypes = [HANDLE, LPVOID, c_size_t, DWORD, DWORD]
VirtualAllocEx.restype = LPVOID

## VirtualFreeEx
VirtualFreeEx = k32.VirtualFreeEx
VirtualFreeEx.argtypes = [HANDLE, LPVOID, c_size_t, DWORD]
VirtualFreeEx.restype = BOOL

## VirtualQueryEx
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.argtypes = [HANDLE, LPCVOID, POINTER(MEMORY_BASIC_INFORMATION), c_size_t]
VirtualQueryEx.restype = c_size_t

## VirtualProtectEx
VirtualProtectEx = k32.VirtualProtectEx
VirtualProtectEx.argtypes = [HANDLE, LPCVOID, c_size_t, DWORD, PDWORD]
VirtualProtectEx.restype = c_size_t

## WriteProcessMemory
WriteProcessMemory = k32.WriteProcessMemory
WriteProcessMemory.argtypes = [HANDLE, LPVOID, LPCVOID, c_size_t, POINTER(c_size_t)]
WriteProcessMemory.restype = BOOL


def jump_instruction(_from: int, _to: int) -> bytearray:
    # 4 bytes long address because 32 bits
    # signed because offset can be negative
    # +5 (length of instruction) because offset is from next instruction
    offset = (_to - (_from + 5)).to_bytes(4, sys.byteorder, signed=True)
    return bytearray(b"\xE9") + offset


def convert_pattern(pattern: str | bytearray) -> bytearray:
    if isinstance(pattern, str):
        return bytearray.fromhex(pattern)
    return pattern


class ReadWriteMemory:

    process: read_write_memory.Process

    def __init__(self, process_name: str):
        rwm = read_write_memory.ReadWriteMemory()

        self.process = rwm.get_process_by_name(process_name)
        self.process.open()

        atexit.register(self.release)

    def release(self):
        self.process.close()

    def scan(
        self,
        pattern: str | bytearray,
        page_begin: int = 0,
        size: int = None,
        exp_page_protect: DWORD = None,
        exp_page_size: c_size_t = None,
    ) -> tuple[int, int, bytearray]:
        """
        Returns address where pattern was found, last scanned page start and page buffer
        """

        if isinstance(pattern, str):
            pattern = bytes.fromhex(pattern)

        if size is None:
            size = 0x800000000 - page_begin

        bytes_read = c_ulonglong()
        old_protect = DWORD()
        mbi = MEMORY_BASIC_INFORMATION()

        VirtualQueryEx(self.process.handle, page_begin, byref(mbi), sizeof(mbi))

        curr = page_begin
        while curr < page_begin + size:

            if (
                # Failed VirtualQueryEx
                not VirtualQueryEx(self.process.handle, curr, byref(mbi), sizeof(mbi))
                # Incorrect rights
                or mbi.State != MEM_COMMIT
                or mbi.Protect == PAGE_NOACCESS
                # Not the expected page protection
                or exp_page_protect
                and mbi.Protect != exp_page_protect
                # Not the expected page size
                or exp_page_size
                and mbi.RegionSize != exp_page_size
            ):
                curr += mbi.RegionSize
                continue

            bytearray_buffer = bytearray(mbi.RegionSize)
            buffer = (c_ubyte * mbi.RegionSize).from_buffer(bytearray_buffer)

            if VirtualProtectEx(
                self.process.handle,
                mbi.BaseAddress,
                mbi.RegionSize,
                PAGE_EXECUTE_READWRITE,
                byref(old_protect),
            ):
                print(
                    f"{hex(curr)} -> {hex(curr + mbi.RegionSize)} | size: {mbi.RegionSize}, protect: {hex(old_protect.value)}"
                )

                ReadProcessMemory(
                    self.process.handle,
                    mbi.BaseAddress,
                    byref(buffer),
                    mbi.RegionSize,
                    byref(bytes_read),
                )

                VirtualProtectEx(
                    self.process.handle,
                    mbi.BaseAddress,
                    mbi.RegionSize,
                    old_protect,
                    pointer(old_protect),
                )

                offset = bytearray_buffer.find(pattern)

                if offset != -1:
                    return curr + offset, curr, bytearray_buffer

            curr += mbi.RegionSize

        return None, None, None

    def read_double(self, ptr: int) -> int:
        try:
            rb = self.process.readByte(ptr, length=8)
            rb = "".join([b.lstrip(r"0x").rjust(2, "0") for b in rb])
            rb = bytearray.fromhex(rb)
            return int(struct.unpack("d", rb)[0])
        except Exception as e:
            print(e)
            return None

    def write(self, dest: int, value: str | bytearray) -> bool:
        bytes_w = c_size_t()
        try:
            if isinstance(value, str):
                value = bytearray.fromhex(value)
            else:
                value = value.copy()
            length = len(value)
            WriteProcessMemory(
                self.process.handle,
                dest,
                (c_char * length).from_buffer(value),
                length,
                pointer(bytes_w),
            )
        except Exception as e:
            print(e)
        return bool(bytes_w.value)

    def fill(self, start: int, end: int, value: int) -> bool:
        bytes_w = c_size_t()
        try:
            length = end - start
            values = length * [value]
            buff = (c_byte * length)(*values)
            WriteProcessMemory(
                self.process.handle,
                start,
                (c_byte * length).from_buffer(buff),
                length,
                pointer(bytes_w),
            )
        except Exception as e:
            print(e)
        return bool(bytes_w.value)
