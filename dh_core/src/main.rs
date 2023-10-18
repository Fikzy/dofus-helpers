#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

pub mod dll_embeder;
pub mod hook;

use crate::hook::GlobalHook;
use dh_utils;

use flexi_logger::{Duplicate, FileSpec, Logger};
use std::sync::mpsc;
use tray_item::{IconSource, TrayItem};

enum Message {
    Quit,
}

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

    let icon = IconSource::Resource("mana-potion");
    let mut tray = TrayItem::new("Dofus Helpers", icon).unwrap();

    let (tx, rx) = mpsc::sync_channel(1);

    tray.add_menu_item("Quit", move || {
        tx.send(Message::Quit).unwrap();
    })
    .unwrap();

    let dll_path = dll_embeder::generate_dll();
    let _hook = GlobalHook::new(&dll_path, "hook_callback");
    log::debug!("{:?}", _hook);

    loop {
        match rx.recv().unwrap() {
            Message::Quit => {
                break;
            }
        }
    }
}
