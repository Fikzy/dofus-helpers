use dirs;
use ini::Ini;
use std::fs::{self, OpenOptions};
use std::path::PathBuf;

pub fn get_app_dir() -> PathBuf {
    let path = dirs::home_dir()
        .expect("Couldn't find home directory")
        .join(".dofus_helpers");
    fs::create_dir_all(&path).expect("Unable to create directory");
    path
}

fn get_app_config_path() -> PathBuf {
    get_app_dir().join("config.ini")
}

pub fn get_app_config() -> Ini {
    let config_path = get_app_config_path();
    OpenOptions::new()
        .write(true)
        .create(true)
        .open(&config_path)
        .unwrap();
    ini::Ini::load_from_file(config_path).unwrap()
}

pub fn save_app_config(config: &Ini) {
    let config_path = get_app_config_path();
    config
        .write_to_file(config_path)
        .expect("Unable to write file");
}
