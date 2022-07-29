#![windows_subsystem = "windows"]

pub mod patch;
pub mod pattern;
pub mod process;
pub mod utils;

use winapi::um::winuser;

use patch::Patch;
use pattern::Pattern;

use crate::patch::{FillNOPPatch, PatchEnum, ReplacementPatch};

fn main() {
    env_logger::init();

    let dofus_client_main_marker: Pattern =
        Pattern::new("F1 * * * F0 * * D0 30 57 2A D5 30 EF * * * * * * * 65 01 20 80 * 6D 05");

    let autotravel_patches: Vec<PatchEnum> = vec![
        // RoleplayWorldFrame
        ReplacementPatch::new(
            "11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * D0 66 * * 12 * * * F0",
            "12",
        )
        .into(),
        ReplacementPatch::new(
            "11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * D0 66 * * 12 * * * EF",
            "12",
        )
        .into(),
        ReplacementPatch::new(
            "11 10 00 00 F0 * * 60 * * 46 * * * * 4F * * * * F0 * * 26",
            "12",
        )
        .into(),
        // MountAutoTripManager
        // - createNextMessage
        ReplacementPatch::new("26 61 * * 01 F0 * * D0 62 04", "27").into(),
        ReplacementPatch::new("26 61 * * 01 F0 * * D0 62 05", "27").into(),
        ReplacementPatch::new("26 61 * * 01 F0 * * D0 62 09", "27").into(),
        // - initNewTrip
        FillNOPPatch::new(
            "F0 * * D0 66 * * * 66 * * 80 * * D6 F0 * * D2 66 * * 96",
            "F0 * * D0 26 68 * * * F0 * * 60 * * D0 66 * * * 66 * * D0",
        )
        .into(),
        // CartographyBase
        ReplacementPatch::new("12 * * * F0 * * D1 F0", "11").into(),
        // MapFlagMenuMaker
        ReplacementPatch::new("12 * * * 29 62 07 82 76 2A 11", "10 0C 00 00").into(),
        // CharacterDisplacementManager
        FillNOPPatch::new(
            "F1 * * * F0 * D0 30 20 80 * * 63 0C 20 80",
            "D0 D1 D2 D3 46 * * * * 80 * 63 0B",
        )
        .into(),
    ];

    let process = match process::get_process_pid("Dofus.exe") {
        Ok(pid) => process::Process::new(pid).unwrap(),
        _ => {
            popup(
                "Unable to find game process.\n\
                Make sure the game is open and on the authentication screen.",
            );
            log::error!("Unable to find game process.");
            std::process::exit(1);
        }
    };

    // Find memory page that contains game bytecode
    let scan_result = match process.scan_pages(dofus_client_main_marker, None) {
        Ok(sr) => sr,
        _ => {
            popup(
                "Failed to find main class marker.\n\
                Something went horribly wrong.",
            );
            log::error!("Failed to find main class marker.");
            std::process::exit(1);
        }
    };

    // Apply patches
    for patch in autotravel_patches {
        if !patch.apply(&scan_result, &process) {
            popup(
                "Failed to apply patch.\n\
                The patch may already be applied.\n\
                Otherwise, make sure the game is on the authentication screen.",
            );
            log::error!("Failed to apply patch.");
            std::process::exit(1);
        }
    }

    popup("Successfully patched!");
    log::info!("Successfully patched!");
}

fn popup(text: &str) {
    unsafe {
        let mut l_text: Vec<u16> = text.encode_utf16().collect();
        l_text.push(0);
        let l_title: Vec<u16> = "Dofus Helper\0".encode_utf16().collect();
        winuser::MessageBoxW(
            std::ptr::null_mut(),
            l_text.as_ptr(),
            l_title.as_ptr(),
            winuser::MB_OK | winuser::MB_ICONINFORMATION,
        );
    }
}
