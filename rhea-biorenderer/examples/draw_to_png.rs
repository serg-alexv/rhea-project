use image::{ImageBuffer, Rgba};
use rhea_biorenderer::{draw, FourCC, VideoFrame};

fn main() -> anyhow::Result<()> {
    let width = 800;
    let height = 600;

    println!("Creating frame {}x{}...", width, height);
    let mut frame = VideoFrame::new(width, height, FourCC::BGRA);

    println!("Drawing checkerboard...");
    draw::checkerboard(&mut frame, 40);

    println!("Drawing some rectangles...");
    draw::rect(&mut frame, 100, 100, 200, 150, 255, 0, 0, 200); // Blueish
    draw::rect(&mut frame, 400, 300, 100, 100, 0, 255, 0, 150); // Greenish

    frame.validate()?;

    println!("Converting BGRA to RGBA for PNG export...");
    // image crate expects RGBA, we have BGRA
    let mut rgba_data = vec![0u8; frame.data.len()];
    for i in (0..frame.data.len()).step_by(4) {
        rgba_data[i] = frame.data[i + 2]; // R
        rgba_data[i + 1] = frame.data[i + 1]; // G
        rgba_data[i + 2] = frame.data[i]; // B
        rgba_data[i + 3] = frame.data[i + 3]; // A
    }

    let img: ImageBuffer<Rgba<u8>, Vec<u8>> = ImageBuffer::from_raw(width, height, rgba_data)
        .ok_or_else(|| anyhow::anyhow!("Failed to create image buffer"))?;

    let out_path = "out.png";
    img.save(out_path)?;

    println!("Success! Saved to {}", out_path);
    Ok(())
}
