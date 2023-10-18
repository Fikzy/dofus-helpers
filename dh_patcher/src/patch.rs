use crate::pattern::Pattern;
use crate::process::{PageScanResult, Process};
use crate::utils;

pub trait Patch {
    fn apply(&self, scan_result: &PageScanResult, process: &Process) -> bool;
}

pub enum PatchEnum {
    ReplacementPatch(ReplacementPatch),
    FillNOPPatch(FillNOPPatch),
}

impl From<ReplacementPatch> for PatchEnum {
    fn from(patch: ReplacementPatch) -> Self {
        PatchEnum::ReplacementPatch(patch)
    }
}

impl From<FillNOPPatch> for PatchEnum {
    fn from(patch: FillNOPPatch) -> Self {
        PatchEnum::FillNOPPatch(patch)
    }
}

impl Patch for PatchEnum {
    fn apply(&self, scan_result: &PageScanResult, process: &Process) -> bool {
        match self {
            PatchEnum::ReplacementPatch(patch) => patch.apply(scan_result, process),
            PatchEnum::FillNOPPatch(patch) => patch.apply(scan_result, process),
        }
    }
}

pub struct ReplacementPatch {
    pub pattern: Pattern,
    pub replacement: Vec<u8>,
}

impl ReplacementPatch {
    pub fn new(pattern: &str, replacement: &str) -> Self {
        Self {
            pattern: Pattern::new(pattern),
            replacement: utils::parse_bytearray(replacement),
        }
    }
}

impl Patch for ReplacementPatch {
    fn apply(&self, scan_result: &PageScanResult, process: &Process) -> bool {
        if let Some(ptr) = self.pattern.scan(&scan_result.page_data) {
            if !process.write(scan_result.page_address + ptr, &self.replacement) {
                log::error!("Failed to write patch to memory.");
                return false;
            }
        } else {
            log::error!("Pattern not found. Failed to apply patch.");
            return false;
        }
        true
    }
}

pub struct FillNOPPatch {
    pub start_pattern: Pattern,
    pub end_pattern: Pattern,
}

impl FillNOPPatch {
    pub fn new(start_pattern: &str, end_pattern: &str) -> Self {
        Self {
            start_pattern: Pattern::new(start_pattern),
            end_pattern: Pattern::new(end_pattern),
        }
    }
}

impl Patch for FillNOPPatch {
    fn apply(&self, scan_result: &PageScanResult, process: &Process) -> bool {
        let start = self.start_pattern.scan(&scan_result.page_data);
        let end = self.end_pattern.scan(&scan_result.page_data);
        if let (Some(start_ptr), Some(end_ptr)) = (start, end) {
            let lenght = end_ptr - start_ptr;
            if !process.write(scan_result.page_address + start_ptr, &vec![0x02; lenght]) {
                log::error!("Failed to write patch to memory.");
                return false;
            }
        } else {
            log::error!("Pattern not found. Failed to apply patch.");
            return false;
        }
        true
    }
}
