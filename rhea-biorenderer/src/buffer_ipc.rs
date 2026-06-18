use std::fs::{OpenOptions, File};
use std::path::PathBuf;
use std::sync::atomic::{AtomicU16, AtomicU64, Ordering};
use memmap2::{MmapMut, Mmap};
use anyhow::{Result, anyhow, ensure};
use crate::buffer_types::{VideoFrame, FourCC};
use crc32fast::Hasher;

// Header Layout (exactly 80 bytes, no padding):
// magic(4) version(2) state(2) seq(8) ts(8) w(4) h(4) stride(4) fourcc(4) dlen(4) crc(4) res(32)
const MAGIC: u32 = 0x52484541;
const VERSION: u16 = 1;
const HEADER_SIZE: usize = 80;

const STATE_OFFSET: usize = 6;
const SEQ_OFFSET: usize = 8;
const CRC_OFFSET: usize = 44;
const TS_OFFSET: usize = 16;
const W_OFFSET: usize = 24;
const H_OFFSET: usize = 28;
const STRIDE_OFFSET: usize = 32;
const FOURCC_OFFSET: usize = 36;
const LEN_OFFSET: usize = 40;

pub struct ShmFrameWriter {
    map: MmapMut,
    _file: File,
}

impl ShmFrameWriter {
    #[cfg(not(target_os = "windows"))]
    pub fn create(name: &str, capacity: usize) -> Result<Self> {
        let path = PathBuf::from(format!("/tmp/rhea_{}.shm", name));
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(&path)?;
        
        file.set_len((HEADER_SIZE + capacity) as u64)?;
        let mut map = unsafe { MmapMut::map_mut(&file)? };
        map.fill(0);
        
        // Write persistent header parts once
        unsafe {
            let ptr = map.as_mut_ptr();
            std::ptr::write_unaligned(ptr as *mut u32, MAGIC);
            std::ptr::write_unaligned(ptr.add(4) as *mut u16, VERSION);
        }
        
        Ok(Self { map, _file: file })
    }

    #[cfg(target_os = "windows")]
    pub fn create(_name: &str, _capacity: usize) -> Result<Self> {
        Err(anyhow!("windows not implemented yet"))
    }

    pub fn write(&mut self, frame: &VideoFrame) -> Result<()> {
        frame.validate()?;
        
        let ptr = self.map.as_mut_ptr();
        unsafe {
            // 1. state = WRITING (1)
            let state = &*(ptr.add(STATE_OFFSET) as *const AtomicU16);
            state.store(1, Ordering::Release);
            
            // 2. seq++
            let seq_atomic = &*(ptr.add(SEQ_OFFSET) as *const AtomicU64);
            let seq_value = seq_atomic.fetch_add(1, Ordering::Relaxed) + 1;

            let ts = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)?
                .as_nanos() as u64;
            let fourcc_u32 = frame.fourcc.as_u32();
            let data_len = frame.data.len() as u32;

            // 3. Write all header fields except CRC
            std::ptr::write_unaligned(ptr.add(TS_OFFSET) as *mut u64, ts);
            std::ptr::write_unaligned(ptr.add(W_OFFSET) as *mut u32, frame.width);
            std::ptr::write_unaligned(ptr.add(H_OFFSET) as *mut u32, frame.height);
            std::ptr::write_unaligned(ptr.add(STRIDE_OFFSET) as *mut u32, frame.stride);
            std::ptr::write_unaligned(ptr.add(FOURCC_OFFSET) as *mut u32, fourcc_u32);
            std::ptr::write_unaligned(ptr.add(LEN_OFFSET) as *mut u32, data_len);
            std::ptr::write_unaligned(ptr.add(CRC_OFFSET) as *mut u32, 0);

            // 4. Copy payload
            std::ptr::copy_nonoverlapping(
                frame.data.as_ptr(),
                ptr.add(HEADER_SIZE),
                frame.data.len()
            );

            // 5. Compute CRC with deterministic field-by-field hashing
            let mut hasher = Hasher::new();
            hasher.update(&MAGIC.to_le_bytes());
            hasher.update(&VERSION.to_le_bytes());
            hasher.update(&2u16.to_le_bytes());          // READY
            hasher.update(&seq_value.to_le_bytes());     // value loaded from AtomicU64
            hasher.update(&ts.to_le_bytes());
            hasher.update(&frame.width.to_le_bytes());
            hasher.update(&frame.height.to_le_bytes());
            hasher.update(&frame.stride.to_le_bytes());
            hasher.update(&fourcc_u32.to_le_bytes());
            hasher.update(&data_len.to_le_bytes());
            hasher.update(&frame.data);
            let crc = hasher.finalize();

            // 6. Write CRC
            std::ptr::write_unaligned(ptr.add(CRC_OFFSET) as *mut u32, crc);

            // 7. state = READY (2)
            state.store(2, Ordering::Release);
        }
        
        Ok(())
    }
}

pub struct ShmFrameReader {
    map: Mmap,
    _file: File,
}

impl ShmFrameReader {
    #[cfg(not(target_os = "windows"))]
    pub fn open(name: &str) -> Result<Self> {
        let path = PathBuf::from(format!("/tmp/rhea_{}.shm", name));
        let file = OpenOptions::new().read(true).write(true).open(&path)?;
        let map = unsafe { Mmap::map(&file)? };
        
        let magic = unsafe { std::ptr::read_unaligned(map.as_ptr() as *const u32) };
        ensure!(magic == MAGIC, "Invalid magic");
        
        Ok(Self { map, _file: file })
    }

    #[cfg(target_os = "windows")]
    pub fn open(_name: &str) -> Result<Self> {
        Err(anyhow!("windows not implemented yet"))
    }

    pub fn read(&mut self) -> Result<Option<VideoFrame>> {
        let ptr = self.map.as_ptr();
        let state_atomic = unsafe { &*(ptr.add(STATE_OFFSET) as *const AtomicU16) };
        
        if state_atomic.load(Ordering::Acquire) != 2 {
            return Ok(None);
        }

        unsafe {
            // Read all fields via AtomicU64 and unaligned reads
            let seq_value = std::ptr::read_unaligned(ptr.add(SEQ_OFFSET) as *const u64);
            let ts = std::ptr::read_unaligned(ptr.add(TS_OFFSET) as *const u64);
            let width = std::ptr::read_unaligned(ptr.add(W_OFFSET) as *const u32);
            let height = std::ptr::read_unaligned(ptr.add(H_OFFSET) as *const u32);
            let stride = std::ptr::read_unaligned(ptr.add(STRIDE_OFFSET) as *const u32);
            let fourcc_u32 = std::ptr::read_unaligned(ptr.add(FOURCC_OFFSET) as *const u32);
            let data_len = std::ptr::read_unaligned(ptr.add(LEN_OFFSET) as *const u32) as usize;
            let expected_crc = std::ptr::read_unaligned(ptr.add(CRC_OFFSET) as *const u32);
            
            // Take payload slice
            let payload = std::slice::from_raw_parts(ptr.add(HEADER_SIZE), data_len);

            // Compute expected CRC with same deterministic logic
            let mut hasher = Hasher::new();
            hasher.update(&MAGIC.to_le_bytes());
            hasher.update(&VERSION.to_le_bytes());
            hasher.update(&2u16.to_le_bytes());          // READY
            hasher.update(&seq_value.to_le_bytes());     // value loaded from AtomicU64
            hasher.update(&ts.to_le_bytes());
            hasher.update(&width.to_le_bytes());
            hasher.update(&height.to_le_bytes());
            hasher.update(&stride.to_le_bytes());
            hasher.update(&fourcc_u32.to_le_bytes());
            hasher.update(&(data_len as u32).to_le_bytes());
            hasher.update(payload);
            let actual_crc = hasher.finalize();

            if actual_crc != expected_crc {
                return Err(anyhow!("CRC mismatch: {:x} != {:x}", expected_crc, actual_crc));
            }

            let frame = VideoFrame {
                width,
                height,
                stride,
                fourcc: FourCC::from_u32(fourcc_u32)?,
                data: payload.to_vec(),
            };

            // Mark as EMPTY (0)
            state_atomic.store(0, Ordering::Release);
            Ok(Some(frame))
        }
    }
}
