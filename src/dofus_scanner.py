from typing import Any

from memory_scanner import *


class PlayerManager:
    _OFF_INVENTORY_WEIGHT = 0x18
    _OFF_INVENTORY_WEIGHT_MAX = 0x20
    _OFF_CURRENT_MAP_PTR = 0xC0
    _OFF_PREV_MAP_PTR = 0xC4


class WorldPointWrapper:
    _OFF_MAP_ID = 0x20


class DofusScanner(MemoryScanner):

    __player_manager_struct_ptr: int = None
    __player_manager_struct_ptr_mem: int = None

    def __init__(self, process_id: int):
        super().__init__(process_id)

    def _player_manager_struct_ptr(self) -> int:

        if not self.__player_manager_struct_ptr:

            if self.__player_manager_struct_ptr_mem is None:
                exit("PlayerManager pointer reader not setup.")

            ptr = self.process.read(self.__player_manager_struct_ptr_mem)
            if ptr:
                self.__player_manager_struct_ptr = ptr
            else:
                print(
                    "PlayerManager structure location unknown, interact with the game to retrieve it."
                )

        return self.__player_manager_struct_ptr

    def read_player_manager_struct_field(
        self, offset: int, read_func=read_write_memory.Process.read
    ) -> Any:
        ptr = self._player_manager_struct_ptr()
        if ptr is None:
            return None
        return read_func(self.process, ptr + offset)

    def setup_player_manager_structure_ptr_reader(self):

        # 19255755 - 8B 90 C8000000        - mov edx,[eax+000000C8]
        # 1925575B - 8D 45 98              - lea eax,[ebp-68]
        # 1925575E - 89 55 F0              - mov [ebp-10],edx
        PATTERN = b"\x8B\x90\xC8\x00\x00\x00\x8D\x45\x98\x89\x55\xF0"
        MASK = b"xxxxxxxxxxxx"

        ptr = scan_ex(
            PATTERN,
            MASK,
            0,
            0x800000000,  # Max 32bit address space?
            self.process.handle,
            exp_page_protect=PAGE_EXECUTE_READ,
            exp_page_size=0xA0000,
        )
        print("ptr:", hex(ptr))

        new_mem_ptr: int = VirtualAllocEx(
            self.process.handle,
            None,
            0x1000,
            MEM_COMMIT | MEM_RESERVE,
            PAGE_EXECUTE_READWRITE,
        )

        self._allocations.append(new_mem_ptr)

        read_ptr_instr_ptr = new_mem_ptr
        self.__player_manager_struct_ptr_mem = new_mem_ptr + 0x20

        overwritten_instr = bytearray(PATTERN[:6])

        jump_to_read_instr = jump_instruction(ptr, read_ptr_instr_ptr)

        read_ptr_instr = (
            overwritten_instr
            + b"\xA3"
            + (self.__player_manager_struct_ptr_mem).to_bytes(4, sys.byteorder)
        )
        jump_back_instr = jump_instruction(
            read_ptr_instr_ptr + len(read_ptr_instr), ptr + len(overwritten_instr)
        )

        self._write_to_memory(ptr, jump_to_read_instr + b"\x90")
        # JUMP + NOP to ensure same size as original

        self._write_to_memory(read_ptr_instr_ptr, read_ptr_instr + jump_back_instr)

        self._injections_to_restore.append((ptr, bytearray(PATTERN[:-1])))

    def read_current_map_ptr(self) -> int:
        return self.read_player_manager_struct_field(PlayerManager._OFF_CURRENT_MAP_PTR)

    def read_current_map_id(self) -> int:
        ptr = self.read_current_map_ptr()
        if ptr is None:
            return None
        return self._read_double(ptr + WorldPointWrapper._OFF_MAP_ID)
