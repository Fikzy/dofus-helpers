from functools import cached_property

from memory_scanner import *


class DofusScanner(MemoryScanner):

    __player_struct_ptr: int = None
    __player_struct_ptr_mem: int

    def __init__(self, process_id: int):
        super().__init__(process_id)

    def player_struct_ptr(self) -> int:
        if not self.__player_struct_ptr:
            ptr = self.process.read(self.__player_struct_ptr_mem)
            if ptr:
                self.__player_struct_ptr = ptr
            else:
                print(
                    "Player struct location unknown, interact with the game to retrieve it."
                )

        return self.__player_struct_ptr

    def setup_player_structure_ptr_reader(self):

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
        self.__player_struct_ptr_mem = new_mem_ptr + 0x20

        print(hex(new_mem_ptr))

        overwritten_instr = bytearray(PATTERN[:6])

        jump_to_read_instr = jump_instruction(ptr, read_ptr_instr_ptr)

        read_ptr_instr = (
            overwritten_instr
            + b"\xA3"
            + (self.__player_struct_ptr_mem).to_bytes(4, sys.byteorder)
        )
        jump_back_instr = jump_instruction(
            read_ptr_instr_ptr + len(read_ptr_instr), ptr + len(overwritten_instr)
        )

        self._write_to_memory(ptr, jump_to_read_instr + b"\x90")
        # JUMP + NOP to ensure same size as original

        self._write_to_memory(read_ptr_instr_ptr, read_ptr_instr + jump_back_instr)

        self._injections_to_restore.append((ptr, bytearray(PATTERN[:-1])))

    def read_inv_weight(self) -> int:
        if self.player_struct_ptr() is None:
            return None
        return self.process.read(self.player_struct_ptr() + 0x18)
