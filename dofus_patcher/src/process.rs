use std::mem::size_of;

use winapi::shared::minwindef::{DWORD, TRUE};
use winapi::shared::ntdef::NULL;
use winapi::um::errhandlingapi::GetLastError;
use winapi::um::handleapi::CloseHandle;
use winapi::um::memoryapi::VirtualQueryEx;
use winapi::um::memoryapi::{ReadProcessMemory, WriteProcessMemory};
use winapi::um::processthreadsapi::OpenProcess;
use winapi::um::winnt::{HANDLE, PROCESS_ALL_ACCESS};
use winapi::um::winnt::{MEMORY_BASIC_INFORMATION, MEM_COMMIT, PAGE_NOACCESS};

use crate::pattern::Pattern;

pub struct Process {
    pub handle: HANDLE,
}

impl Process {
    pub fn new(process_id: DWORD) -> Result<Self, DWORD> {
        unsafe {
            match OpenProcess(PROCESS_ALL_ACCESS, TRUE, process_id) {
                NULL => Err(GetLastError()),
                process => Ok(Process { handle: process }),
            }
        }
    }
}

impl Drop for Process {
    fn drop(&mut self) {
        unsafe { CloseHandle(self.handle) };
    }
}

pub struct PageScanResult {
    pub page_address: usize,
    pub page_data: Vec<u8>,
}

impl Process {
    pub fn read(&self, address: usize, size: usize) -> Vec<u8> {
        let mut buffer: Vec<u8> = vec![0; size];
        unsafe {
            ReadProcessMemory(
                self.handle,
                address as _,
                buffer.as_mut_ptr() as _,
                buffer.len(),
                std::ptr::null_mut(),
            );
        }
        buffer
    }

    pub fn write(&self, address: usize, data: &[u8]) -> bool {
        unsafe {
            WriteProcessMemory(
                self.handle,
                address as _,
                data.as_ptr() as _,
                data.len(),
                std::ptr::null_mut(),
            ) == TRUE
        }
    }

    pub fn scan_pages(
        &self,
        pattern: Pattern,
        start_page: Option<usize>,
    ) -> Result<PageScanResult, String> {
        unsafe {
            let mut page_address: usize = start_page.unwrap_or(0);
            let mut mem_info: MEMORY_BASIC_INFORMATION = std::mem::zeroed();

            while VirtualQueryEx(
                self.handle,
                page_address as _,
                &mut mem_info,
                size_of::<MEMORY_BASIC_INFORMATION>(),
            ) != 0
            {
                if mem_info.State == MEM_COMMIT && mem_info.State != PAGE_NOACCESS {
                    // Read memory
                    let page_data = self.read(page_address, mem_info.RegionSize);

                    log::debug!("{:x}: {}", page_address, page_data.len());

                    if pattern.scan(&page_data).is_some() {
                        return Ok(PageScanResult {
                            page_address,
                            page_data,
                        });
                    }
                }

                page_address += mem_info.RegionSize;
            }
            Err("Pattern not found.".to_string())
        }
    }
}
