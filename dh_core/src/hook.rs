use libloading::os::windows::{Library, Symbol};
use winapi::{shared::minwindef, shared::windef, um::winuser};

#[derive(Debug)]
pub struct GlobalHook {
    id: windef::HHOOK,
}

impl GlobalHook {
    pub fn new(lib_path: &str, fct_name: &str) -> Self {
        let lib = unsafe { Library::new(lib_path).expect("Unable to load DLL") };
        let hook_callback: Symbol<unsafe extern "system" fn(i32, usize, isize) -> isize> = unsafe {
            lib.get(fct_name.as_bytes())
                .expect("Unable to load function")
        };
        let id = unsafe {
            winuser::SetWindowsHookExA(
                winuser::WH_SHELL,
                Some(*hook_callback),
                lib.into_raw() as minwindef::HINSTANCE,
                0,
            )
        };
        if id.is_null() {
            log::error!("Unable to set hook");
            panic!("Unable to set hook")
        }
        GlobalHook { id }
    }
}

impl Drop for GlobalHook {
    fn drop(&mut self) {
        log::debug!("Dropping {:?}", self);
        unsafe {
            winuser::UnhookWindowsHookEx(self.id);
            // Send a dummy message to ensure the dll is unloaded
            // https://stackoverflow.com/a/54834158/15873956
            winuser::SendNotifyMessageA(winuser::HWND_BROADCAST, winuser::WM_NULL, 0, 0);
        }
    }
}
