use ini::Ini;
use native_windows_gui as nwg;
use nwg::NativeUi;
use std::{cell::RefCell, ops::Deref, rc::Rc};

use dh_utils;

#[derive(Default)]
pub struct SystemTray {
    window: nwg::MessageWindow,
    embed: nwg::EmbedResource,
    icon: nwg::Icon,
    tray: nwg::TrayNotification,
    tray_menu: nwg::Menu,
    skip_confirmation_popup_item: nwg::MenuItem,
    exit_item: nwg::MenuItem,
}

fn read_skip_confirmation_popup_option(config: Option<Ini>) -> bool {
    let config = config.unwrap_or_else(|| dh_utils::get_app_config());
    str::parse::<bool>(
        config
            .get_from(Some("autotravel"), "skip_confirmation_popup")
            .unwrap_or("true"),
    )
    .unwrap_or(true)
}

impl SystemTray {
    fn show_menu(&self) {
        let (x, y) = nwg::GlobalCursor::position();
        self.tray_menu.popup(x, y);
    }

    fn toggle_skip_confirmation_popup_option(&self) {
        let mut config = dh_utils::get_app_config();
        let skip_confirmation_popup = !read_skip_confirmation_popup_option(Some(config.clone()));

        self.skip_confirmation_popup_item
            .set_checked(skip_confirmation_popup);

        config.set_to(
            Some("autotravel"),
            "skip_confirmation_popup".to_string(),
            skip_confirmation_popup.to_string(),
        );
        dh_utils::save_app_config(&config);
    }

    fn exit(&self) {
        nwg::stop_thread_dispatch();
    }
}

pub struct SystemTrayUi {
    inner: Rc<SystemTray>,
    default_handler: RefCell<Vec<nwg::EventHandler>>,
}

impl NativeUi<SystemTrayUi> for SystemTray {
    fn build_ui(mut data: SystemTray) -> Result<SystemTrayUi, nwg::NwgError> {
        use nwg::Event as E;

        // Resources
        // uses executable-name.rc by default
        nwg::EmbedResource::builder().build(&mut data.embed)?;

        nwg::Icon::builder()
            .source_embed(Some(&data.embed))
            .source_embed_str(Some("MAIN_ICON"))
            .build(&mut data.icon)?;

        // Controls
        nwg::MessageWindow::builder().build(&mut data.window)?;

        nwg::TrayNotification::builder()
            .parent(&data.window)
            .icon(Some(&data.icon))
            .build(&mut data.tray)?;

        nwg::Menu::builder()
            .popup(true)
            .parent(&data.window)
            .build(&mut data.tray_menu)?;

        nwg::MenuItem::builder()
            .text("Skip confirmation popup")
            .check(read_skip_confirmation_popup_option(None))
            .parent(&data.tray_menu)
            .build(&mut data.skip_confirmation_popup_item)?;

        nwg::MenuItem::builder()
            .text("Exit")
            .parent(&data.tray_menu)
            .build(&mut data.exit_item)?;

        // Wrap-up
        let ui = SystemTrayUi {
            inner: Rc::new(data),
            default_handler: Default::default(),
        };

        // Events
        let evt_ui = Rc::downgrade(&ui.inner);
        let handle_events = move |evt, _evt_data: nwg::EventData, handle: nwg::ControlHandle| {
            if let Some(evt_ui) = evt_ui.upgrade() {
                match evt {
                    E::OnContextMenu => {
                        if &handle == &evt_ui.tray {
                            SystemTray::show_menu(&evt_ui);
                        }
                    }
                    E::OnMenuItemSelected => {
                        if &handle == &evt_ui.skip_confirmation_popup_item {
                            SystemTray::toggle_skip_confirmation_popup_option(&evt_ui);
                        } else if &handle == &evt_ui.exit_item {
                            SystemTray::exit(&evt_ui);
                        }
                    }
                    _ => {}
                }
            }
        };

        ui.default_handler
            .borrow_mut()
            .push(nwg::full_bind_event_handler(
                &ui.window.handle,
                handle_events,
            ));

        return Ok(ui);
    }
}

impl Drop for SystemTrayUi {
    // To make sure that everything is freed without issues, the default handler must be unbound.
    fn drop(&mut self) {
        let mut handlers = self.default_handler.borrow_mut();
        for handler in handlers.drain(0..) {
            nwg::unbind_event_handler(&handler);
        }
    }
}

impl Deref for SystemTrayUi {
    type Target = SystemTray;

    fn deref(&self) -> &SystemTray {
        &self.inner
    }
}
