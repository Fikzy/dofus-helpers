from memory_scanner import *


class DofusScanner(MemoryScanner):

    player_struct_ptr: int = None

    def __init__(self, process_id: int):
        super().__init__(process_id)

        self.player_struct_ptr = None

    def setup_player_structure_ptr_reader(self):

        # 19255755 - 8B 90 C8000000        - mov edx,[eax+000000C8]
        # 1925575B - 8D 45 98              - lea eax,[ebp-68]
        # 1925575E - 89 55 F0              - mov [ebp-10],edx
        PATTERN = b"\x8B\x90\xC8\x00\x00\x00\x8D\x45\x98\x89\x55\xF0"
        MASK = b"xxxxxxxxxxxx"

        # ptr = scan_ex(PATTERN, MASK, 0, 0x7FFF0000, self.process.handle)
        # print("ptr:", hex(ptr))
        ptr = 0x19255755

        new_mem_ptr: int = VirtualAllocEx(
            self.process.handle,
            None,
            0x1000,
            MEM_COMMIT | MEM_RESERVE,
            PAGE_EXECUTE_READWRITE,
        )

        self._allocations.append(new_mem_ptr)

        read_ptr_instr_ptr = new_mem_ptr
        self.player_struct_ptr = new_mem_ptr + 0x20

        jump_to_instr = jump_instruction(read_ptr_instr_ptr, ptr)
        read_ptr_instr = (
            bytearray(b"\x8B\x90\xC8\x00\x00\x00")
            + bytearray(b"\xA3")
            + (self.player_struct_ptr).to_bytes(4, sys.byteorder)
            + jump_instruction(ptr - 6, read_ptr_instr_ptr)
        )

        self._write_to_memory(ptr, jump_to_instr)
        self._write_to_memory(read_ptr_instr_ptr, read_ptr_instr)

        self._injections_to_restore.append((ptr, bytearray(PATTERN[:-1])))

    def read_inv_weight(self) -> int:
        if self.player_struct_ptr is None:
            print(
                "PlayerCharacterManager location unknown, move around in the game to obtain it."
            )
            return None
        return self.process.read(self.player_struct_ptr + 0x18)

    # def read_map_id(self) -> int:
    #     OFFSET = 0x68
    #     try:
    #         mapid_ptr = self.process.read(self.player_struct_ptr)
    #         if not mapid_ptr:
    #             print("MapID location unknown, change map once to obtain it.")
    #             return None
    #         return self.__read_double(mapid_ptr + OFFSET)
    #     except Exception as e:
    #         print(e)
    #         return None
