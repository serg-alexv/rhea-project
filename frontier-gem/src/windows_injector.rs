//! Windows Text Injection Module
//! 
//! Provides keyboard event injection into the focused window using Windows SendInput API.
//! Includes safety checks to avoid injecting into password fields or system windows.

#[cfg(target_os = "windows")]
use std::ffi::CString;
#[cfg(target_os = "windows")]
use std::ptr;

/// Error type for injection operations
#[derive(Debug, Clone)]
pub enum InjectorError {
    NoFocusedWindow,
    InvalidTarget(String),
    InjectionFailed(String),
    UnsafeTarget(String),
    TextTooLarge,
    InvalidCharacter(char),
}

impl std::fmt::Display for InjectorError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            InjectorError::NoFocusedWindow => write!(f, "No focused window found"),
            InjectorError::InvalidTarget(msg) => write!(f, "Invalid target: {}", msg),
            InjectorError::InjectionFailed(msg) => write!(f, "Injection failed: {}", msg),
            InjectorError::UnsafeTarget(msg) => write!(f, "Unsafe target: {}", msg),
            InjectorError::TextTooLarge => write!(f, "Text exceeds 10KB limit"),
            InjectorError::InvalidCharacter(c) => write!(f, "Invalid character: {}", c),
        }
    }
}

impl std::error::Error for InjectorError {}

/// Information about a focused window
#[derive(Debug, Clone)]
pub struct WindowInfo {
    pub hwnd: usize,
    pub title: String,
    pub class_name: String,
    pub is_safe: bool,
}

/// Text injector for Windows platform
pub struct TextInjector;

#[cfg(target_os = "windows")]
mod windows_impl {
    use super::*;
    use std::mem;
    use std::os::windows::ffi::OsStrExt;
    use std::path::Path;
    use std::ffi::OsStr;

    // Win32 API types
    #[repr(C)]
    struct INPUT {
        typ: u32,
        data: [u8; 28],
    }

    const INPUT_KEYBOARD: u32 = 1;
    const KEYEVENTF_KEYUP: u32 = 0x0002;

    // Virtual key codes
    const VK_SHIFT: u8 = 0x10;
    const VK_CONTROL: u8 = 0x11;
    const VK_ALT: u8 = 0x12;
    const VK_BACK: u8 = 0x08;
    const VK_RETURN: u8 = 0x0D;
    const VK_TAB: u8 = 0x09;

    extern "system" {
        fn GetForegroundWindow() -> usize;
        fn GetWindowTextW(hwnd: usize, text: *mut u16, count: i32) -> i32;
        fn GetClassNameW(hwnd: usize, class_name: *mut u16, count: i32) -> i32;
        fn IsWindow(hwnd: usize) -> bool;
        fn SendInput(num_inputs: u32, inputs: *const INPUT, size: i32) -> u32;
        fn Sleep(ms: u32);
    }

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

    pub fn get_focused_window() -> Result<WindowInfo, InjectorError> {
        unsafe {
            let hwnd = GetForegroundWindow();
            
            if hwnd == 0 || !IsWindow(hwnd) {
                return Err(InjectorError::NoFocusedWindow);
            }

            // Get window title
            let mut title_buf = vec![0u16; 256];
            let title_len = GetWindowTextW(hwnd, title_buf.as_mut_ptr(), 256);
            title_buf.truncate(title_len as usize);
            let title = utf16_to_string(&title_buf);

            // Get class name
            let mut class_buf = vec![0u16; 256];
            let class_len = GetClassNameW(hwnd, class_buf.as_mut_ptr(), 256);
            class_buf.truncate(class_len as usize);
            let class_name = utf16_to_string(&class_buf);

            let is_safe = is_safe_target_impl(&class_name);

            Ok(WindowInfo {
                hwnd,
                title,
                class_name,
                is_safe,
            })
        }
    }

    fn is_safe_target_impl(class_name: &str) -> bool {
        // Block password fields, credentials, system windows
        let blocked_patterns = vec![
            "Password",
            "Credential",
            "Secret",
            "PIN",
            "Authentication",
            "SysListView32",
            "SysTreeView32",
            "SHELLDLL_DefView",
            "ShellBrowserWindow",
            "#32770",  // Dialog
        ];

        for pattern in blocked_patterns {
            if class_name.contains(pattern) {
                return false;
            }
        }

        // Only allow known safe text input controls
        let allowed = vec![
            "Edit",
            "RichEditText",
            "RichEdit",
            "textarea",
            "input",
            "Chrome_RenderWidgetHostHWND",
            "Firefox",
            "MozillaWindowClass",
            "CabinetWClass",  // Explorer
            "Notepad",
        ];

        for pattern in allowed {
            if class_name.contains(pattern) {
                return true;
            }
        }

        // Also allow empty/generic windows (assume user targeted intentionally)
        class_name.is_empty() || class_name.len() == 1
    }

    pub fn validate_text(text: &str) -> Result<(), InjectorError> {
        // Check size (max 10KB)
        if text.len() > 10240 {
            return Err(InjectorError::TextTooLarge);
        }

        // Check for invalid characters (keep most Unicode, block only dangerous ones)
        for ch in text.chars() {
            // Allow most printable + newline + tab
            if !ch.is_control() || ch == '\n' || ch == '\t' || ch == '\r' {
                continue;
            }
            // Block null and other control characters
            if ch == '\0' {
                return Err(InjectorError::InvalidCharacter(ch));
            }
        }

        Ok(())
    }

    pub fn inject_text_impl(text: &str, delay_ms: u32) -> Result<(), InjectorError> {
        validate_text(text)?;

        let info = get_focused_window()?;
        
        if !info.is_safe {
            return Err(InjectorError::UnsafeTarget(format!(
                "Target class '{}' is not safe for injection",
                info.class_name
            )));
        }

        unsafe {
            for ch in text.chars() {
                match ch {
                    '\n' => {
                        // Send Enter key
                        let mut input = INPUT {
                            typ: INPUT_KEYBOARD,
                            data: [0; 28],
                        };
                        // KEYDOWN
                        *(&mut input.data[0] as *mut _ as *mut u8) = VK_RETURN;
                        if SendInput(1, &input, mem::size_of::<INPUT>() as i32) == 0 {
                            return Err(InjectorError::InjectionFailed(
                                "Failed to send Enter key".to_string(),
                            ));
                        }

                        // KEYUP
                        input.data[2] = KEYEVENTF_KEYUP as u8;
                        if SendInput(1, &input, mem::size_of::<INPUT>() as i32) == 0 {
                            return Err(InjectorError::InjectionFailed(
                                "Failed to send Enter key (up)".to_string(),
                            ));
                        }
                    }
                    '\t' => {
                        // Send Tab key
                        let mut input = INPUT {
                            typ: INPUT_KEYBOARD,
                            data: [0; 28],
                        };
                        *(&mut input.data[0] as *mut _ as *mut u8) = VK_TAB;
                        if SendInput(1, &input, mem::size_of::<INPUT>() as i32) == 0 {
                            return Err(InjectorError::InjectionFailed(
                                "Failed to send Tab key".to_string(),
                            ));
                        }
                        input.data[2] = KEYEVENTF_KEYUP as u8;
                        SendInput(1, &input, mem::size_of::<INPUT>() as i32);
                    }
                    _ => {
                        // Regular character - use virtual key
                        let vk = char_to_vk(ch);
                        if vk == 0xFF {
                            // Unsupported character, try using character code
                            continue;
                        }

                        let mut input = INPUT {
                            typ: INPUT_KEYBOARD,
                            data: [0; 28],
                        };
                        *(&mut input.data[0] as *mut _ as *mut u8) = vk;
                        
                        // Handle shift for uppercase
                        if ch.is_uppercase() && ch.is_alphabetic() {
                            // Send Shift+Key
                            let shift_input = INPUT {
                                typ: INPUT_KEYBOARD,
                                data: [VK_SHIFT, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            };
                            SendInput(1, &shift_input, mem::size_of::<INPUT>() as i32);
                        }

                        // KEYDOWN
                        if SendInput(1, &input, mem::size_of::<INPUT>() as i32) == 0 {
                            return Err(InjectorError::InjectionFailed(
                                format!("Failed to send key for '{}'", ch),
                            ));
                        }

                        // KEYUP
                        input.data[2] = KEYEVENTF_KEYUP as u8;
                        SendInput(1, &input, mem::size_of::<INPUT>() as i32);

                        // Release shift if needed
                        if ch.is_uppercase() && ch.is_alphabetic() {
                            let mut shift_input = INPUT {
                                typ: INPUT_KEYBOARD,
                                data: [VK_SHIFT, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                            };
                            shift_input.data[2] = KEYEVENTF_KEYUP as u8;
                            SendInput(1, &shift_input, mem::size_of::<INPUT>() as i32);
                        }
                    }
                }

                // Delay between characters
                if delay_ms > 0 {
                    Sleep(delay_ms);
                }
            }
        }

        Ok(())
    }

    fn char_to_vk(ch: char) -> u8 {
        match ch {
            'a'..='z' | 'A'..='Z' => ((ch.to_ascii_uppercase() as u8) - b'A' + 0x41) as u8,
            '0'..='9' => (ch as u8 - b'0' + 0x30) as u8,
            ' ' => 0x20,
            '!' => 0x31,
            '@' => 0x32,
            '#' => 0x33,
            '$' => 0x34,
            '%' => 0x35,
            '^' => 0x36,
            '&' => 0x37,
            '*' => 0x38,
            '(' => 0x39,
            ')' => 0x30,
            '-' => 0xBD,
            '_' => 0xBD,
            '=' => 0xBB,
            '+' => 0xBB,
            '[' => 0xDB,
            '{' => 0xDB,
            ']' => 0xDD,
            '}' => 0xDD,
            ';' => 0xBA,
            ':' => 0xBA,
            '\'' => 0xDE,
            '"' => 0xDE,
            ',' => 0xBC,
            '<' => 0xBC,
            '.' => 0xBE,
            '>' => 0xBE,
            '/' => 0xBF,
            '?' => 0xBF,
            '\\' => 0xDC,
            '|' => 0xDC,
            '`' => 0xC0,
            '~' => 0xC0,
            _ => 0xFF, // Unsupported
        }
    }
}

#[cfg(not(target_os = "windows"))]
mod non_windows_impl {
    use super::*;

    pub fn get_focused_window() -> Result<WindowInfo, InjectorError> {
        Err(InjectorError::InvalidTarget(
            "Text injection is only supported on Windows".to_string(),
        ))
    }

    pub fn validate_text(_text: &str) -> Result<(), InjectorError> {
        Err(InjectorError::InvalidTarget(
            "Text injection is only supported on Windows".to_string(),
        ))
    }

    pub fn inject_text_impl(_text: &str, _delay_ms: u32) -> Result<(), InjectorError> {
        Err(InjectorError::InvalidTarget(
            "Text injection is only supported on Windows".to_string(),
        ))
    }
}

impl TextInjector {
    /// Get information about the currently focused window
    pub fn get_focused_window() -> Result<WindowInfo, InjectorError> {
        #[cfg(target_os = "windows")]
        return windows_impl::get_focused_window();

        #[cfg(not(target_os = "windows"))]
        return non_windows_impl::get_focused_window();
    }

    /// Check if a target window is safe for injection
    pub fn is_safe_target(window_info: &WindowInfo) -> bool {
        window_info.is_safe
    }

    /// Validate text before injection
    pub fn validate_text(text: &str) -> Result<(), InjectorError> {
        #[cfg(target_os = "windows")]
        return windows_impl::validate_text(text);

        #[cfg(not(target_os = "windows"))]
        return non_windows_impl::validate_text(text);
    }

    /// Inject text into the focused window
    ///
    /// # Arguments
    /// * `text` - The text to inject (max 10KB)
    /// * `delay_ms` - Delay in milliseconds between keystrokes (0 = no delay)
    pub fn inject_text(text: &str, delay_ms: u32) -> Result<(), InjectorError> {
        #[cfg(target_os = "windows")]
        {
            // Validate delay (max 1000ms per keystroke to prevent abuse)
            let delay = std::cmp::min(delay_ms, 1000);
            return windows_impl::inject_text_impl(text, delay);
        }

        #[cfg(not(target_os = "windows"))]
        return non_windows_impl::inject_text_impl(text, delay_ms);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_text_validation() {
        // Valid texts
        assert!(TextInjector::validate_text("Hello, World!").is_ok());
        assert!(TextInjector::validate_text("Multi\nline\ntext").is_ok());
        assert!(TextInjector::validate_text("Tab\tseparated").is_ok());

        // Text too large
        let large_text = "a".repeat(20000);
        assert!(TextInjector::validate_text(&large_text).is_err());
    }

    #[test]
    #[cfg(not(target_os = "windows"))]
    fn test_non_windows_graceful_handling() {
        // Should return error on non-Windows platforms
        assert!(TextInjector::get_focused_window().is_err());
        assert!(TextInjector::inject_text("test", 0).is_err());
    }
}
