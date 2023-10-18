use log;
use std::fs;
use std::path::{Path, PathBuf};

use dh_utils;

const DLL_NAME: &'static str = "dofus-helpers.dll";
#[cfg(debug_assertions)]
const DLL_DATA: &'static [u8] = include_bytes!("..\\..\\target\\debug\\dh_dll.dll");
#[cfg(not(debug_assertions))]
const DLL_DATA: &'static [u8] = include_bytes!("..\\..\\target\\release\\dh_dll.dll");

fn get_dll_path() -> PathBuf {
    dh_utils::get_app_dir().join(DLL_NAME)
}

pub fn generate_dll() -> String {
    let dll_path = get_dll_path();
    if !Path::new(&dll_path).exists() || cfg!(debug_assertions) {
        fs::write(&dll_path, DLL_DATA).expect("Unable to write file");
        log::debug!("Generated DLL at {:?}", dll_path);
    }
    dll_path.to_str().unwrap().to_string()
}
