import atexit
import ctypes
import struct
import sys
import time
from ctypes import *
from ctypes.wintypes import *

import dofus_scanner
import exec_handler
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


class HEAPLIST32(Structure):
    _fields_ = [
        ("dwSize", c_size_t),
        ("th32ProcessID", DWORD),
        ("th32HeapID", DWORD),
        ("dwFlags", DWORD),
    ]


class HEAPENTRY32(Structure):
    _fields_ = [
        ("dwSize", c_size_t),
        ("hHandle", HANDLE),
        ("dwAddress", DWORD),
        ("dwBlockSize", DWORD),
        ("dwFlags", DWORD),
        ("dwLockCount", DWORD),
        ("dwResvd", DWORD),
        ("th32ProcessID", DWORD),
        ("th32HeapID", DWORD),
    ]


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


## CreateToolhelp32Snapshot
CreateToolhelp32Snapshot = k32.CreateToolhelp32Snapshot
CreateToolhelp32Snapshot.argtypes = [DWORD, DWORD]
CreateToolhelp32Snapshot.restype = HANDLE

## CloseHandle
CloseHandle = k32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL

## GetLastError
GetLastError = k32.GetLastError
GetLastError.argtypes = []
GetLastError.restype = DWORD

## GetMappedFileNameA
GetMappedFileNameA = psapi.GetMappedFileNameA
# GetMappedFileNameA.argtypes = [HANDLE, LPVOID, LPSTR, DWORD]
GetMappedFileNameA.restype = DWORD

## Heap32ListFirst
Heap32ListFirst = k32.Heap32ListFirst
Heap32ListFirst.argtypes = [HANDLE, POINTER(HEAPLIST32)]
Heap32ListFirst.restype = BOOL

## Heap32ListNext
Heap32ListNext = k32.Heap32ListNext
Heap32ListNext.argtypes = [HANDLE, POINTER(HEAPLIST32)]
Heap32ListNext.restype = BOOL

## Heap32First
Heap32First = k32.Heap32First
Heap32First.argtypes = [POINTER(HEAPENTRY32), DWORD, DWORD]
Heap32First.restype = BOOL

## Heap32Next
Heap32Next = k32.Heap32Next
Heap32Next.argtypes = [POINTER(HEAPENTRY32)]
Heap32Next.restype = BOOL

## Module32First
Module32First = k32.Module32First
Module32First.argtypes = [HANDLE, POINTER(MODULEENTRY32)]
Module32First.restype = BOOL

## Module32Next
Module32Next = k32.Module32Next
Module32Next.argtypes = [HANDLE, POINTER(MODULEENTRY32)]
Module32Next.restype = BOOL

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


def iterate_heap(proc_id: DWORD) -> MODULEENTRY32:

    snap_h: HANDLE = CreateToolhelp32Snapshot(TH32CS_SNAPHEAPLIST, proc_id)

    if snap_h == INVALID_HANDLE_VALUE:
        print(f"CreateToolhelp32Snapshot failed: {GetLastError()}\n")
        return

    heap_list = HEAPLIST32()
    heap_list.dwSize = sizeof(HEAPLIST32)

    if not Heap32ListFirst(snap_h, pointer(heap_list)):
        print(f"Heap32ListFirst failed: {GetLastError()}\n")
        return

    heap_entry = HEAPENTRY32()
    heap_entry.dwSize = sizeof(HEAPENTRY32)

    while True:
        print(
            f"dwSize: {heap_list.dwSize}, th32ProcessID: {heap_list.th32ProcessID}, th32HeapID: {heap_list.th32HeapID}, dwFlags: {heap_list.dwFlags}"
        )

        if heap_list.dwFlags != 1:
            if Heap32First(
                pointer(heap_entry), heap_list.th32ProcessID, heap_list.th32HeapID
            ):
                while True:
                    print(
                        f"{hex(heap_entry.dwAddress)} -> {hex(heap_entry.dwAddress + heap_entry.dwBlockSize)} ({heap_entry.dwBlockSize})"
                    )

                    heap_entry.dwSize = sizeof(HEAPENTRY32)
                    if not Heap32Next(heap_entry):
                        break

            else:
                print(f"Heap32First failed: {GetLastError()}")

        heap_list.dwSize = sizeof(HEAPLIST32)

        if not Heap32ListNext(snap_h, pointer(heap_list)):
            break

    print()
    CloseHandle(snap_h)


def get_module(proc_id: DWORD, mod_name: bytes) -> MODULEENTRY32:

    snap_h: HANDLE = CreateToolhelp32Snapshot(
        TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, proc_id
    )

    if snap_h == INVALID_HANDLE_VALUE:
        print(f"CreateToolhelp32Snapshot failed: {GetLastError()}\n")
        return None

    mod_entry = MODULEENTRY32()
    mod_entry.dwSize = sizeof(MODULEENTRY32)

    if Module32First(snap_h, pointer(mod_entry)):
        while True:
            if mod_entry.szModule == mod_name:
                return mod_entry
            if not Module32Next(snap_h, pointer(mod_entry)):
                break

    CloseHandle(snap_h)

    return None


def scan_basic(
    pattern: bytearray, begin: int, size: int, mask: bytearray = None
) -> int:

    pattern_len = len(pattern)

    if mask:
        for i in range(size):
            found = True
            for j in range(pattern_len):
                val = cast(begin + i + j, POINTER(c_ubyte)).contents.value
                # 63 == ?
                if mask[j] != 63 and pattern[j] != val:
                    found = False
                    break
            if found:
                return begin + i
    else:
        for i in range(size):
            found = True
            for j in range(pattern_len):
                val = cast(begin + i + j, POINTER(c_ubyte)).contents.value
                if pattern[j] != val:
                    found = False
                    break
            if found:
                return begin + i

    return 0


def jump_instruction(_from: int, _to: int) -> bytearray:
    # 4 bytes long address because 32 bits
    # signed because offset can be negative
    # +5 (length of instruction) because offset is from next instruction
    offset = (_to - (_from + 5)).to_bytes(4, sys.byteorder, signed=True)
    return bytearray(b"\xE9") + offset


class ReadWriteMemory:

    process: read_write_memory.Process
    _allocations: list[int]
    _injections_to_restore: list[tuple[int, bytearray]]

    def __init__(self, process_id: int):
        rwm = read_write_memory.ReadWriteMemory()

        self.process = rwm.get_process_by_id(process_id)
        self.process.open()

        self._allocations = []
        self._injections_to_restore = []

        atexit.register(self.release)

    def release(self):
        """
        Must be called in order to roll back injections and free page allocations.
        """

        print("~ReadWriteMemory()")

        # Restore injections
        for ptr, buffer in self._injections_to_restore:
            self.write(ptr, buffer)

        # Free up allocations
        for ptr in self._allocations:
            VirtualFreeEx(self.process.handle, ptr, 0, MEM_RELEASE)

    def scan(
        self,
        pattern: str | bytearray,
        page_begin: int = 0,
        size: int = None,
        mask: bytearray = None,
        exp_page_protect: DWORD = None,
        exp_page_size: c_size_t = None,
    ) -> tuple[int, int]:
        """
        Returns address where pattern was found as well as last scanned page start
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

            buffer = (c_ubyte * mbi.RegionSize)()

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

                internal_addr = scan_basic(
                    pattern, addressof(buffer), bytes_read.value, mask
                )

                if internal_addr:
                    return curr + (internal_addr - addressof(buffer)), curr

            curr += mbi.RegionSize

    def scan_mod(
        self,
        pattern: str | bytearray,
        mod_entry: MODULEENTRY32,
        mask: bytearray = None,
    ) -> int:

        if isinstance(pattern, str):
            pattern = bytes.fromhex(pattern)

        return self.scan(
            pattern,
            cast(mod_entry.modBaseAddr, c_void_p).value,
            mod_entry.modBaseSize,
            mask,
        )

    def read_double(self, ptr: int) -> int:
        try:
            rb = self.process.readByte(ptr, length=8)
            rb = "".join([b.lstrip(r"0x").rjust(2, "0") for b in rb])
            rb = bytearray.fromhex(rb)
            return int(struct.unpack("d", rb)[0])
        except Exception as e:
            print(e)
            return None

    def write(self, dest: int, value: str | bytearray) -> c_size_t:
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
        return bytes_w

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
        return bool(bytes_w)


def walk_mem_maps(h_proc: HANDLE):

    mbi = MEMORY_BASIC_INFORMATION()

    curr = 0

    buffer = (c_char * 256)()

    while curr < 0x7FFF0000:

        VirtualQueryEx(h_proc, curr, byref(mbi), sizeof(mbi))

        if mbi.State != MEM_COMMIT or mbi.Protect == PAGE_NOACCESS:
            curr += mbi.RegionSize
            continue

        GetMappedFileNameA(h_proc, curr, byref(buffer), len(buffer))

        name: str = buffer.value.decode("utf-8")

        print(f"{hex(curr)} -> {hex(curr + mbi.RegionSize)} ({mbi.RegionSize}) {name}")

        curr += mbi.RegionSize


def iterate_modules(proc_id: DWORD):

    snap_h: HANDLE = CreateToolhelp32Snapshot(
        TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, proc_id
    )

    if snap_h == INVALID_HANDLE_VALUE:
        print(f"CreateToolhelp32Snapshot failed: {GetLastError()}\n")
        return None

    mod_entry = MODULEENTRY32()
    mod_entry.dwSize = sizeof(MODULEENTRY32)

    if Module32First(snap_h, pointer(mod_entry)):
        while True:

            print("th32ModuleID:", mod_entry.th32ModuleID)
            print("th32ProcessID:", mod_entry.th32ProcessID)
            print("GlblcntUsage:", mod_entry.GlblcntUsage)
            print("ProccntUsage:", mod_entry.ProccntUsage)
            print("modBaseAddr:", hex(cast(mod_entry.modBaseAddr, c_void_p).value))
            print("modBaseSize:", mod_entry.modBaseSize)
            print("hModule:", mod_entry.hModule)
            print("szModule:", mod_entry.szModule)
            print("szExePath:", mod_entry.szExePath)
            print()

            if not Module32Next(snap_h, pointer(mod_entry)):
                break

    CloseHandle(snap_h)

    return None


if __name__ == "__main__":

    handler = exec_handler.ExecHandler(".* - Dofus .*")

    start = time.time()

    scanner = dofus_scanner.DofusScanner(handler.get_pid())
    scanner._setup_player_character_manager_ptr_reader()

    print(f"Took: {time.time() - start:.2f}s")

    print("map_id:", scanner.read_current_map_id())

    time.sleep(10)

    print("map_id:", scanner.read_current_map_id())