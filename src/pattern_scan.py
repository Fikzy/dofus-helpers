from ctypes import *
from ctypes.wintypes import *
import struct

import exec_handler
import read_write_memory

k32 = WinDLL("kernel32", use_last_error=True)

INVALID_HANDLE_VALUE = -1
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010

MEM_COMMIT = 0x1000
PAGE_NOACCESS = 0x01
PAGE_EXECUTE_READWRITE = 0x40


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

## Module32First
Module32First = k32.Module32First
Module32First.argtypes = [HANDLE, POINTER(MODULEENTRY32)]
Module32First.restype = BOOL

## Module32Next
Module32Next = k32.Module32Next
Module32Next.argtypes = [HANDLE, POINTER(MODULEENTRY32)]
Module32Next.restype = BOOL

## VirtualQueryEx
VirtualQueryEx = k32.VirtualQueryEx
VirtualQueryEx.argtypes = [HANDLE, LPCVOID, POINTER(MEMORY_BASIC_INFORMATION), c_size_t]
VirtualQueryEx.restype = c_size_t

## VirtualProtectEx
VirtualProtectEx = k32.VirtualProtectEx
VirtualProtectEx.argtypes = [HANDLE, LPCVOID, c_size_t, DWORD, PDWORD]
VirtualProtectEx.restype = c_size_t

## ReadProcessMemory
ReadProcessMemory = k32.ReadProcessMemory
ReadProcessMemory.argtypes = [HANDLE, LPCVOID, LPVOID, c_size_t, POINTER(c_size_t)]
ReadProcessMemory.restype = BOOL


def get_module(proc_id: c_ulong, mod_name: bytes) -> MODULEENTRY32:

    snap_h: HANDLE = CreateToolhelp32Snapshot(
        TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, proc_id
    )

    if snap_h != INVALID_HANDLE_VALUE:
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


def scan_basic(pattern: bytearray, mask: bytearray, begin: int, size: int) -> int:

    pattern_len = len(pattern)

    for i in range(size):
        found = True

        for j in range(pattern_len):

            val = cast(begin + i + j, POINTER(c_ubyte)).contents.value

            # print(hex(val), end=" ")

            # 63 == ?
            # if mask[j] != 63 and pattern[j] != val:
            if pattern[j] != val:
                found = False
                break

        # print()

        if found:
            return begin + i

    return 0


def scan_ex(
    pattern: bytearray,
    mask: bytearray,
    begin: int,
    size: int,
    h_proc: HANDLE,
) -> int:

    match: int = 0
    bytes_read = c_ulonglong()
    old_protect = DWORD()
    mbi = MEMORY_BASIC_INFORMATION()
    # mbi.RegionSize = 0x1000

    VirtualQueryEx(h_proc, begin, byref(mbi), sizeof(mbi))

    curr = begin
    while curr < begin + size:

        if not VirtualQueryEx(h_proc, curr, byref(mbi), sizeof(mbi)):
            print(
                f"skipping : {hex(curr)} -> {hex(curr + mbi.RegionSize)} ({mbi.RegionSize}) VirtualQueryEx failed"
            )
            curr += mbi.RegionSize
            continue
        if mbi.State != MEM_COMMIT or mbi.Protect == PAGE_NOACCESS:
            print(
                f"skipping : {hex(curr)} -> {hex(curr + mbi.RegionSize)} ({mbi.RegionSize}) State != MEM_COMMIT or Protect == PAGE_NOACCESS"
            )
            curr += mbi.RegionSize
            continue

        buffer = (c_ubyte * mbi.RegionSize)()

        if VirtualProtectEx(
            h_proc,
            mbi.BaseAddress,
            mbi.RegionSize,
            PAGE_EXECUTE_READWRITE,
            byref(old_protect),
        ):
            print(f"{hex(curr)} -> {hex(curr + mbi.RegionSize)} ({mbi.RegionSize})")

            result = ReadProcessMemory(
                h_proc,
                mbi.BaseAddress,
                byref(buffer),
                mbi.RegionSize,
                byref(bytes_read),
            )

            # print(
            #     f"read success: {result}, bytes_read: {bytes_read.value}, error: {get_last_error()}"
            # )
            # print(addressof(buffer))
            # print(bytearray(buffer))

            VirtualProtectEx(
                h_proc,
                mbi.BaseAddress,
                mbi.RegionSize,
                old_protect,
                pointer(old_protect),
            )

            internal_addr = scan_basic(
                pattern, mask, addressof(buffer), bytes_read.value
            )

            if internal_addr:
                match = curr + (internal_addr - addressof(buffer))
                break

        else:
            print(
                f"skipping : {hex(curr)} -> {hex(curr + mbi.RegionSize)} ({mbi.RegionSize}) VirtualProtectEx failed"
            )

        curr += mbi.RegionSize

    return match


def scan_mod_ex(
    pattern: bytearray,
    mask: bytearray,
    mod_entry: MODULEENTRY32,
    h_proc: HANDLE,
) -> int:
    return scan_ex(
        pattern,
        mask,
        cast(mod_entry.modBaseAddr, c_void_p).value,
        mod_entry.modBaseSize,
        h_proc,
    )


if __name__ == "__main__":

    handler = exec_handler.ExecHandler(".* - Dofus .*")

    # mod_entry = get_module(handler.get_pid(), b"Adobe AIR.dll")
    # print("module name:", mod_entry.szModule.decode("utf-8"))
    # base_addr = cast(mod_entry.modBaseAddr, c_void_p).value
    # print(
    #     "module base address:",
    #     base_addr,
    #     hex(base_addr),
    #     "->",
    #     hex(base_addr + mod_entry.modBaseSize),
    # )
    # print("module base size:", mod_entry.modBaseSize)

    rwm = read_write_memory.ReadWriteMemory()
    process = rwm.get_process_by_id(handler.get_pid())
    process.open()

    # print(hex(base_addr + int(0x4D9E07)))  # Adobe AIR.dll + py4D9E07

    # offsets = [0x0113CA28, 0x31C, 0xC, 0x8C, 0x64, 0x10, 0x94, 0xB18]

    # ptr = base_addr
    # for offset in offsets[:-1]:
    #     print(f"{hex(ptr)} + {hex(offset)} -> ", end="")
    #     ptr = process.read(ptr + offset)
    #     print(hex(ptr))

    # ptr += offsets[-1]
    # print(hex(ptr))

    # # map_id_pointer = process.get_pointer(0x62EE0000, offsets)

    # rb = process.readByte(ptr, length=8)
    # rb = "".join([b.lstrip(r"0x").rjust(2, "0") for b in rb])
    # rb = bytearray.fromhex(rb)
    # print(int(struct.unpack("d", rb)[0]))

    pattern = b"\x66\x0f\xd6\x46\x68\x83"
    mask = b"xxxxxx"

    ptr = scan_ex(pattern, mask, 0, 0x0800000000000, process.handle)
    # ptr = scan_ex(pattern, mask, 0x1C1B7000, 0x1E000, process.handle)
    # ptr = scan_ex(pattern, mask, 0x1C000000, 0x200000, process.handle)
    # ptr = scan_mod_ex(pattern, mask, mod_entry, process.handle)
    print("ptr:", hex(ptr))

    process.close()
