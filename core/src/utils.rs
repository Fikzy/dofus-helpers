use dirs;
use std::fs;
use std::path::PathBuf;

pub fn get_app_dir() -> PathBuf {
    let path = dirs::home_dir()
        .expect("Couldn't find home directory")
        .join(".dofus_helpers");
    fs::create_dir_all(&path).expect("Unable to create directory");
    path
}
