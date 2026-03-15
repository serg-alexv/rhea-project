use rhea_biorenderer::{draw, FourCC, ShmFrameWriter, VideoFrame};
use std::thread;
use std::time::Duration;

const REGION_NAME: &str = "demo";
const WIDTH: u32 = 640;
const HEIGHT: u32 = 360;

fn main() -> anyhow::Result<()> {
    let mut writer = ShmFrameWriter::create(REGION_NAME, (WIDTH * HEIGHT * 4) as usize)?;
    let mut tick = 0u32;

    println!("Writing BGRA frames to '{REGION_NAME}'");

    loop {
        let mut frame = VideoFrame::new(WIDTH, HEIGHT, FourCC::BGRA);
        draw::checkerboard(&mut frame, 24);
        let x = tick.wrapping_mul(9) % WIDTH.saturating_sub(160);
        let y = tick.wrapping_mul(5) % HEIGHT.saturating_sub(120);
        draw::rect(&mut frame, x, y, 160, 120, 24, 120, 255, 255);
        draw::rect(&mut frame, WIDTH / 5, HEIGHT / 3, 96, 96, 255, 48, 32, 220);
        frame.validate()?;
        writer.write(&frame)?;
        tick = tick.wrapping_add(1);
        thread::sleep(Duration::from_millis(33));
    }
}
