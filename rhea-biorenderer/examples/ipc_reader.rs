use anyhow::{Context, Result};
use image::{ImageBuffer, Rgba};
use rhea_biorenderer::{FourCC, ShmFrameReader, VideoFrame};
use std::thread;
use std::time::{Duration, Instant};

const REGION_NAME: &str = "demo";

fn main() -> Result<()> {
    let mut reader: Option<ShmFrameReader> = None;
    let mut latest: Option<VideoFrame> = None;
    let mut last_save = Instant::now();

    println!("Waiting for shared region '{REGION_NAME}'");

    loop {
        if reader.is_none() {
            match ShmFrameReader::open(REGION_NAME) {
                Ok(opened) => {
                    println!("Connected to '{REGION_NAME}'");
                    reader = Some(opened);
                }
                Err(_) => {
                    thread::sleep(Duration::from_millis(250));
                    continue;
                }
            }
        };

        if let Some(open_reader) = reader.as_mut() {
            match open_reader.read() {
                Ok(Some(frame)) => latest = Some(frame),
                Ok(None) => {}
                Err(err) => {
                    eprintln!("reader error: {err:#}");
                    reader = None;
                    thread::sleep(Duration::from_millis(100));
                    continue;
                }
            }
        }

        if last_save.elapsed() >= Duration::from_secs(1) {
            if let Some(frame) = latest.as_ref() {
                save_png(frame, "out.png")?;
                println!("Wrote out.png ({}x{})", frame.width, frame.height);
            }
            last_save = Instant::now();
        }

        thread::sleep(Duration::from_millis(10));
    }
}

fn save_png(frame: &VideoFrame, path: &str) -> Result<()> {
    match frame.fourcc {
        FourCC::BGRA => {}
    }

    let mut rgba = vec![0u8; frame.data.len()];
    for offset in (0..frame.data.len()).step_by(4) {
        rgba[offset] = frame.data[offset + 2];
        rgba[offset + 1] = frame.data[offset + 1];
        rgba[offset + 2] = frame.data[offset];
        rgba[offset + 3] = frame.data[offset + 3];
    }

    let image: ImageBuffer<Rgba<u8>, Vec<u8>> =
        ImageBuffer::from_raw(frame.width, frame.height, rgba)
            .context("failed to build RGBA image buffer")?;
    image
        .save(path)
        .with_context(|| format!("failed to save {path}"))?;
    Ok(())
}
