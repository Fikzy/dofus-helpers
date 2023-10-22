pub mod patch;
pub mod pattern;
pub mod process;
pub mod utils;

use dh_utils;

use crate::patch::Patch;
use crate::patch::{FillNOPPatch, PatchEnum, ReplacementPatch};
use crate::pattern::Pattern;

#[derive(Debug)]
pub enum DofusPatcherError {
    ProcessNotFound,
    MainClassMarkerNotFound,
    PatchApplicationFailed,
}

pub fn patch_client(pid: u32) -> Result<(), DofusPatcherError> {
    let dofus_client_main_marker: Pattern =
        Pattern::new("F1 * * * F0 * * D0 30 57 2A D5 30 EF * * * * * * * 65 01 20 80 * 6D 05");

    let mut autotravel_patches: Vec<PatchEnum> = vec![
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

    let config = dh_utils::get_app_config();

    let skip_confirmation_popup = str::parse(
        config
            .get_from(Some("autotravel"), "skip_confirmation_popup")
            .unwrap_or("true"),
    )
    .unwrap_or(true);

    if skip_confirmation_popup {
        autotravel_patches.push(
            // - onRouteFound
            ReplacementPatch::new(
                "12 * * * F0 * * D0 27 68 * * * F0 * * D0 4F * * * * F0 * * 47 F0",
                "11",
            )
            .into(),
        )
    }

    let process = match process::Process::new(pid) {
        Ok(proc) => proc,
        Err(err) => {
            log::error!("Unable to find game process ({})", err);
            Err(DofusPatcherError::ProcessNotFound)?
        }
    };

    // Find memory page that contains game bytecode
    let scan_result = match process.scan_pages(dofus_client_main_marker, None) {
        Ok(sr) => sr,
        _ => {
            log::error!("Failed to find main class marker");
            Err(DofusPatcherError::MainClassMarkerNotFound)?
        }
    };

    // Apply patches
    for patch in autotravel_patches {
        if !patch.apply(&scan_result, &process) {
            log::error!("Failed to apply patch");
            Err(DofusPatcherError::PatchApplicationFailed)?
        }
    }

    log::info!("Successfully patched!");
    Ok(())
}
