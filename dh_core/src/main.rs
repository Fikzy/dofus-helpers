#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

pub mod dll_embeder;
pub mod hook;
pub mod system_tray;

use crate::hook::GlobalHook;
use crate::system_tray::SystemTray;
use dh_utils;

use flexi_logger::{Duplicate, FileSpec, Logger};
use native_windows_gui as nwg;
use nwg::NativeUi;

fn main() {
    let _logger = Logger::try_with_str("debug")
        .unwrap()
        .log_to_file(
            FileSpec::default()
                .directory(dh_utils::get_app_dir())
                .basename("app")
                .suppress_timestamp(),
        )
        .duplicate_to_stdout(Duplicate::All)
        .format(flexi_logger::detailed_format)
        .start();

    let dll_path = dll_embeder::generate_dll();
    let _hook = GlobalHook::new(&dll_path, "hook_callback");
    log::debug!("{:?}", _hook);

    nwg::init().expect("Failed to init Native Windows GUI");
    let _ui = SystemTray::build_ui(Default::default()).expect("Failed to build UI");
    nwg::dispatch_thread_events();
}
