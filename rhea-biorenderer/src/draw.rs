use crate::buffer_types::VideoFrame;

pub fn clear(frame: &mut VideoFrame, b: u8, g: u8, r: u8, a: u8) {
    for y in 0..frame.height {
        for x in 0..frame.width {
            set_pixel(frame, x, y, b, g, r, a);
        }
    }
}

pub fn rect(frame: &mut VideoFrame, x: u32, y: u32, w: u32, h: u32, b: u8, g: u8, r: u8, a: u8) {
    let x_end = (x + w).min(frame.width);
    let y_end = (y + h).min(frame.height);

    for py in y..y_end {
        for px in x..x_end {
            set_pixel(frame, px, py, b, g, r, a);
        }
    }
}

pub fn checkerboard(frame: &mut VideoFrame, size: u32) {
    for y in 0..frame.height {
        for x in 0..frame.width {
            if ((x / size) + (y / size)) % 2 == 0 {
                set_pixel(frame, x, y, 200, 200, 200, 255);
            } else {
                set_pixel(frame, x, y, 50, 50, 50, 255);
            }
        }
    }
}

#[inline]
fn set_pixel(frame: &mut VideoFrame, x: u32, y: u32, b: u8, g: u8, r: u8, a: u8) {
    let offset = (y * frame.stride + x * 4) as usize;
    if offset + 3 < frame.data.len() {
        frame.data[offset] = b;
        frame.data[offset + 1] = g;
        frame.data[offset + 2] = r;
        frame.data[offset + 3] = a;
    }
}
