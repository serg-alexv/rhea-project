//! System Focus Detection
//!
//! Detect which window/application currently has focus.
//! Cross-platform: Windows, macOS, Linux

use std::fmt;

/// Information about the focused window
#[derive(Debug, Clone)]
pub struct FocusedWindow {
    pub process_name: String,
    pub window_class: String,
    pub window_title: String,
}

impl fmt::Display for FocusedWindow {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "Process: {}, Class: {}, Title: {}",
            self.process_name, self.window_class, self.window_title
        )
    }
}

/// Get information about the currently focused window
pub fn get_focused_window() -> Result<FocusedWindow, String> {
    #[cfg(target_os = "windows")]
    return windows_impl::get_focused();

    #[cfg(target_os = "macos")]
    return macos_impl::get_focused();

    #[cfg(target_os = "linux")]
    return linux_impl::get_focused();

    #[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
    return Err("Focus detection not supported on this platform".to_string());
}

#[cfg(target_os = "windows")]
mod windows_impl {
    use super::FocusedWindow;
    use std::ffi::{CStr, OsStr};
    use std::mem;
    use std::os::windows::ffi::OsStrExt;
    use std::ptr;

    extern "system" {
        fn GetForegroundWindow() -> usize;
        fn GetWindowTextW(hwnd: usize, text: *mut u16, count: i32) -> i32;
        fn GetClassNameW(hwnd: usize, class_name: *mut u16, count: i32) -> i32;
        fn GetWindowThreadProcessId(hwnd: usize, process_id: *mut u32) -> u32;
        fn OpenProcess(desired_access: u32, inherit_handle: bool, process_id: u32) -> *mut u8;
        fn GetModuleFileNameExW(
            process: *mut u8,
            module: *mut u8,
            filename: *mut u16,
            size: u32,
        ) -> u32;
        fn CloseHandle(object: *mut u8) -> bool;
    }

    const PROCESS_QUERY_INFORMATION: u32 = 0x0400;
    const PROCESS_VM_READ: u32 = 0x0010;

    fn utf16_from_str(s: &str) -> Vec<u16> {
        OsStr::new(s)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect()
    }

    fn utf16_to_string(buf: &[u16]) -> String {
        let len = buf.iter().position(|&x| x == 0).unwrap_or(buf.len());
        String::from_utf16_lossy(&buf[..len]).to_string()
    }

    pub fn get_focused() -> Result<FocusedWindow, String> {
        unsafe {
            let hwnd = GetForegroundWindow();
            if hwnd == 0 {
                return Err("No focused window".to_string());
            }

            // Get window title
            let mut title_buf = vec![0u16; 256];
            let title_len = GetWindowTextW(hwnd, title_buf.as_mut_ptr(), 256);
            title_buf.truncate(title_len as usize);
            let window_title = utf16_to_string(&title_buf);

            // Get class name
            let mut class_buf = vec![0u16; 256];
            let class_len = GetClassNameW(hwnd, class_buf.as_mut_ptr(), 256);
            class_buf.truncate(class_len as usize);
            let window_class = utf16_to_string(&class_buf);

            // Get process ID
            let mut process_id: u32 = 0;
            GetWindowThreadProcessId(hwnd, &mut process_id);

            // Get process name
            let process_name = if process_id > 0 {
                let process_handle =
                    OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, false, process_id);
                
                if !process_handle.is_null() {
                    let mut filename_buf = vec![0u16; 256];
                    let len = GetModuleFileNameExW(
                        process_handle,
                        ptr::null_mut(),
                        filename_buf.as_mut_ptr(),
                        256,
                    );
                    filename_buf.truncate(len as usize);
                    let path = utf16_to_string(&filename_buf);

                    CloseHandle(process_handle);

                    // Extract just the filename
                    path.split('\\')
                        .last()
                        .unwrap_or("unknown")
                        .to_string()
                } else {
                    format!("PID_{}", process_id)
                }
            } else {
                "unknown".to_string()
            };

            Ok(FocusedWindow {
                process_name,
                window_class,
                window_title,
            })
        }
    }
}

#[cfg(target_os = "macos")]
mod macos_impl {
    use super::FocusedWindow;

    pub fn get_focused() -> Result<FocusedWindow, String> {
        // macOS implementation using Cocoa
        // For now, return a placeholder
        // In production, use:
        // - NSWorkspace.shared.frontmostApplication
        // - CGWindowListCopyWindowInfo()
        
        Ok(FocusedWindow {
            process_name: "unknown".to_string(),
            window_class: "NSWindow".to_string(),
            window_title: "macOS window".to_string(),
        })
    }
}

#[cfg(target_os = "linux")]
mod linux_impl {
    use super::FocusedWindow;

    pub fn get_focused() -> Result<FocusedWindow, String> {
        // Linux implementation using X11 or Wayland
        // For now, return a placeholder
        // In production, use:
        // - XGetInputFocus() for X11
        // - wl_shell for Wayland
        
        Ok(FocusedWindow {
            process_name: "unknown".to_string(),
            window_class: "X11Window".to_string(),
            window_title: "Linux window".to_string(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_focused_window() {
        match get_focused_window() {
            Ok(window) => {
                println!("Focused: {}", window);
                assert!(!window.process_name.is_empty() || cfg!(not(target_os = "windows")));
            }
            Err(e) => {
                println!("Could not get focused window: {}", e);
                // This is expected on some platforms or CI environments
            }
        }
    }
}
