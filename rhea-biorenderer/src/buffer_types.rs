use anyhow::{ensure, Result};

pub const FOURCC_BGRA: u32 = 0x41524742;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FourCC {
    BGRA, // 0x41524742
}

impl FourCC {
    pub fn as_u32(self) -> u32 {
        match self {
            Self::BGRA => FOURCC_BGRA,
        }
    }

    pub fn to_u32(self) -> u32 {
        self.as_u32()
    }

    pub fn from_u32(value: u32) -> Result<Self> {
        match value {
            FOURCC_BGRA => Ok(Self::BGRA),
            _ => anyhow::bail!("unsupported FourCC: 0x{value:08x}"),
        }
    }
}

#[derive(Clone, Debug)]
pub struct VideoFrame {
    pub width: u32,
    pub height: u32,
    pub stride: u32,
    pub fourcc: FourCC,
    pub data: Vec<u8>,
}

impl VideoFrame {
    pub fn new(width: u32, height: u32, fourcc: FourCC) -> Self {
        let stride = width * 4;
        let data = vec![0u8; (stride * height) as usize];
        Self {
            width,
            height,
            stride,
            fourcc,
            data,
        }
    }

    pub fn validate(&self) -> Result<()> {
        ensure!(
            self.stride >= self.width * 4,
            "Stride too small: {} < {}",
            self.stride,
            self.width * 4
        );
        let expected_size = (self.height * self.stride) as usize;
        ensure!(
            self.data.len() == expected_size,
            "Data length mismatch: expected {}, got {}",
            expected_size,
            self.data.len()
        );
        Ok(())
    }
}
