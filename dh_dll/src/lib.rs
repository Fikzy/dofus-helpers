use flexi_logger::{Age, Cleanup, Criterion, FileSpec, Logger, Naming};
use log;
use notify_rust::Notification;
use std::slice;
use winapi::{shared::windef, um::winuser};

use dh_patcher;
use dh_utils;

#[no_mangle]
pub extern "system" fn hook_callback(n_code: i32, w_param: usize, l_param: isize) -> isize {
    if n_code < 0 {
        unsafe {
            return winuser::CallNextHookEx(0 as windef::HHOOK, n_code, w_param, l_param);
        }
    }
    if n_code != winuser::HSHELL_WINDOWCREATED {
        return 0;
    }

    let window_handle = w_param as windef::HWND;

    let title_length = unsafe { winuser::GetWindowTextLengthA(window_handle) };
    let mut title_raw = Vec::<i8>::with_capacity((title_length).try_into().unwrap());

    unsafe {
        winuser::GetWindowTextA(window_handle, title_raw.as_mut_ptr(), title_length + 1);
    }

    let title_u8_raw = unsafe {
        slice::from_raw_parts(title_raw.as_ptr() as *const u8, (title_length + 1) as usize)
    };
    let title = String::from_utf8_lossy(&title_u8_raw[..(title_length as usize)]);

    let mut pid = 0;
    unsafe {
        winuser::GetWindowThreadProcessId(window_handle, &mut pid);
    }

    if title != "Dofus" {
        return 0;
    }

    let _logger = Logger::try_with_str("info")
        .unwrap()
        .log_to_file(FileSpec::default().directory(dh_utils::get_app_dir().join("dll_logs")))
        .rotate(
            Criterion::Age(Age::Day),
            Naming::Timestamps,
            Cleanup::KeepLogFiles(5),
        )
        .append()
        .format(flexi_logger::detailed_format)
        .start();

    log::info!("{} ({})", title, pid);

    match dh_patcher::patch_client(pid as u32) {
        Ok(_) => {
            Notification::new()
                .summary("Dofus Helpers")
                .body("Successfully patched!")
                .show()
                .unwrap();
        }
        Err(err) => {
            Notification::new()
                .summary("Dofus Helpers")
                .body(format!("Error: {:?}", err).as_str())
                .show()
                .unwrap();
        }
    }

    0
}
