// Windows-only clipboard backend focused on TEXT and BGRA images.
// Cargo.toml: windows = "0.56" (or compatible)

#![cfg(target_os = "windows")]

use std::{ptr, thread, time::Duration};

use windows::{
    core::Result as WinResult,
    Win32::{
        Foundation::{HANDLE, HWND},
        System::Memory::{GlobalAlloc, GlobalLock, GlobalSize, GlobalUnlock, GMEM_MOVEABLE},
        UI::Shell::CF_DIBV5,
        UI::WindowsAndMessaging::CF_UNICODETEXT,
        UI::WindowsAndMessaging::{
            CloseClipboard, EmptyClipboard, GetClipboardData, OpenClipboard, SetClipboardData,
        },
    },
};

#[derive(Debug)]
pub enum ClipboardError {
    Win(windows::core::Error),
    Utf16,
    ClipboardEmpty,
    InvalidImage,
}

impl From<windows::core::Error> for ClipboardError {
    fn from(e: windows::core::Error) -> Self {
        ClipboardError::Win(e)
    }
}

pub type ClipResult<T> = std::result::Result<T, ClipboardError>;

#[derive(Clone, Copy, Debug)]
pub enum FourCC {
    BGRA, // little-endian: B,G,R,A in memory
}

#[derive(Debug)]
pub struct ClipboardImage {
    pub width: u32,
    pub height: u32,
    pub stride: u32,
    pub fourcc: FourCC,
    pub data: Vec<u8>,
}

fn open_clipboard_with_retry(hwnd: HWND) -> WinResult<()> {
    // Clipboard can be busy; retry a few times.
    for _ in 0..20 {
        unsafe {
            if OpenClipboard(hwnd).as_bool() {
                return Ok(());
            }
        }
        thread::sleep(Duration::from_millis(10));
    }
    // last try to get a proper error
    unsafe { OpenClipboard(hwnd).ok() }
}

pub fn set_text(text: &str) -> ClipResult<()> {
    let mut wide: Vec<u16> = text.encode_utf16().collect();
    wide.push(0);

    unsafe {
        open_clipboard_with_retry(HWND(0))?;
        EmptyClipboard().ok()?;

        let bytes = wide.len() * 2;
        let hmem =
            GlobalAlloc(GMEM_MOVEABLE, bytes).ok_or_else(|| windows::core::Error::from_win32())?;
        let p = GlobalLock(hmem) as *mut u8;
        if p.is_null() {
            CloseClipboard().ok()?;
            return Err(windows::core::Error::from_win32().into());
        }

        ptr::copy_nonoverlapping(wide.as_ptr() as *const u8, p, bytes);
        GlobalUnlock(hmem);

        // After SetClipboardData succeeds, the system owns the memory handle.
        SetClipboardData(CF_UNICODETEXT.0 as u32, HANDLE(hmem.0)).ok()?;
        CloseClipboard().ok()?;
    }

    Ok(())
}

pub fn get_text() -> ClipResult<Option<String>> {
    unsafe {
        open_clipboard_with_retry(HWND(0))?;
        let h = GetClipboardData(CF_UNICODETEXT.0 as u32);
        if h.0 == 0 {
            CloseClipboard().ok()?;
            return Ok(None);
        }
        let p = GlobalLock(HANDLE(h.0)) as *const u16;
        if p.is_null() {
            CloseClipboard().ok()?;
            return Err(windows::core::Error::from_win32().into());
        }

        // find null terminator
        let mut len = 0usize;
        loop {
            let v = *p.add(len);
            if v == 0 {
                break;
            }
            len += 1;
        }

        let slice = std::slice::from_raw_parts(p, len);
        let s = String::from_utf16(slice).map_err(|_| ClipboardError::Utf16)?;
        GlobalUnlock(HANDLE(h.0));
        CloseClipboard().ok()?;
        Ok(Some(s))
    }
}

// BITMAPV5HEADER definition (packed to match Windows layout)
#[repr(C)]
#[derive(Clone, Copy)]
struct BitmapV5Header {
    bV5Size: u32,
    bV5Width: i32,
    bV5Height: i32,
    bV5Planes: u16,
    bV5BitCount: u16,
    bV5Compression: u32,
    bV5SizeImage: u32,
    bV5XPelsPerMeter: i32,
    bV5YPelsPerMeter: i32,
    bV5ClrUsed: u32,
    bV5ClrImportant: u32,
    bV5RedMask: u32,
    bV5GreenMask: u32,
    bV5BlueMask: u32,
    bV5AlphaMask: u32,
    bV5CSType: u32,
    bV5Endpoints: [u32; 9],
    bV5GammaRed: u32,
    bV5GammaGreen: u32,
    bV5GammaBlue: u32,
    bV5Intent: u32,
    bV5ProfileData: u32,
    bV5ProfileSize: u32,
    bV5Reserved: u32,
}

// Constants: BI_BITFIELDS = 3, LCS_sRGB = 0x73524742 ('sRGB')
const BI_BITFIELDS: u32 = 3;
const LCS_SRGB: u32 = 0x7352_4742;

pub fn set_image_bgra(width: u32, height: u32, stride: u32, data: &[u8]) -> ClipResult<()> {
    // Expect BGRA8, bottom-up DIB is default; we will store as top-down by using negative height.
    let expected = (height as usize) * (stride as usize);
    if data.len() < expected {
        return Err(ClipboardError::InvalidImage);
    }

    let header = BitmapV5Header {
        bV5Size: std::mem::size_of::<BitmapV5Header>() as u32,
        bV5Width: width as i32,
        bV5Height: -(height as i32), // top-down
        bV5Planes: 1,
        bV5BitCount: 32,
        bV5Compression: BI_BITFIELDS,
        bV5SizeImage: (height * stride) as u32,
        bV5XPelsPerMeter: 0,
        bV5YPelsPerMeter: 0,
        bV5ClrUsed: 0,
        bV5ClrImportant: 0,
        bV5RedMask: 0x00FF0000,
        bV5GreenMask: 0x0000FF00,
        bV5BlueMask: 0x000000FF,
        bV5AlphaMask: 0xFF000000,
        bV5CSType: LCS_SRGB,
        bV5Endpoints: [0; 9],
        bV5GammaRed: 0,
        bV5GammaGreen: 0,
        bV5GammaBlue: 0,
        bV5Intent: 0,
        bV5ProfileData: 0,
        bV5ProfileSize: 0,
        bV5Reserved: 0,
    };

    let header_bytes = unsafe {
        std::slice::from_raw_parts(
            &header as *const BitmapV5Header as *const u8,
            std::mem::size_of::<BitmapV5Header>(),
        )
    };

    let total = header_bytes.len() + expected;

    unsafe {
        open_clipboard_with_retry(HWND(0))?;
        EmptyClipboard().ok()?;

        let hmem =
            GlobalAlloc(GMEM_MOVEABLE, total).ok_or_else(|| windows::core::Error::from_win32())?;
        let p = GlobalLock(hmem) as *mut u8;
        if p.is_null() {
            CloseClipboard().ok()?;
            return Err(windows::core::Error::from_win32().into());
        }

        ptr::copy_nonoverlapping(header_bytes.as_ptr(), p, header_bytes.len());
        ptr::copy_nonoverlapping(data.as_ptr(), p.add(header_bytes.len()), expected);

        GlobalUnlock(hmem);

        SetClipboardData(CF_DIBV5.0 as u32, HANDLE(hmem.0)).ok()?;
        CloseClipboard().ok()?;
    }

    Ok(())
}

pub fn get_image_bgra() -> ClipResult<Option<ClipboardImage>> {
    unsafe {
        open_clipboard_with_retry(HWND(0))?;
        let h = GetClipboardData(CF_DIBV5.0 as u32);
        if h.0 == 0 {
            CloseClipboard().ok()?;
            return Ok(None);
        }

        let p = GlobalLock(HANDLE(h.0)) as *const u8;
        if p.is_null() {
            CloseClipboard().ok()?;
            return Err(windows::core::Error::from_win32().into());
        }

        let size = GlobalSize(HANDLE(h.0));
        if size < std::mem::size_of::<BitmapV5Header>() {
            GlobalUnlock(HANDLE(h.0));
            CloseClipboard().ok()?;
            return Err(ClipboardError::InvalidImage);
        }

        let hdr = &*(p as *const BitmapV5Header);
        if hdr.bV5BitCount != 32 {
            GlobalUnlock(HANDLE(h.0));
            CloseClipboard().ok()?;
            return Err(ClipboardError::InvalidImage);
        }

        let width = hdr.bV5Width.unsigned_abs();
        let height_raw = hdr.bV5Height;
        let top_down = height_raw < 0;
        let height = (height_raw.unsigned_abs()) as u32;

        let header_len = std::mem::size_of::<BitmapV5Header>();
        let img_bytes = (size as usize).saturating_sub(header_len);
        let stride = (img_bytes as u32) / height.max(1);

        let src = std::slice::from_raw_parts(p.add(header_len), img_bytes);

        // Normalize to top-down BGRA in Vec<u8>.
        let mut out = vec![0u8; img_bytes];
        if top_down {
            out.copy_from_slice(src);
        } else {
            // bottom-up -> flip rows
            let row = stride as usize;
            for y in 0..height as usize {
                let src_y = (height as usize - 1 - y) * row;
                let dst_y = y * row;
                out[dst_y..dst_y + row].copy_from_slice(&src[src_y..src_y + row]);
            }
        }

        GlobalUnlock(HANDLE(h.0));
        CloseClipboard().ok()?;

        Ok(Some(ClipboardImage {
            width,
            height,
            stride,
            fourcc: FourCC::BGRA,
            data: out,
        }))
    }
}
