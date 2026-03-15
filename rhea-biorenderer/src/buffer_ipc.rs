use anyhow::{anyhow, ensure, Context, Result};
use crc32fast::Hasher;
use memmap2::MmapMut;
use std::{
    fs::{File, OpenOptions},
    path::PathBuf,
    sync::atomic::{AtomicU16, AtomicU64, Ordering},
    time::{SystemTime, UNIX_EPOCH},
};

use crate::buffer_types::{FourCC, VideoFrame};

const MAGIC: u32 = 0x5248_4541; // "RHEA"
const VERSION: u16 = 1;

const STATE_EMPTY: u16 = 0;
const STATE_WRITING: u16 = 1;
const STATE_READY: u16 = 2;

// Offsets in shared region (little-endian, unaligned):
// 0  magic u32
// 4  version u16
// 6  state u16 (atomic)
// 8  seq u64 (atomic)
// 16 timestamp_ns u64
// 24 width u32
// 28 height u32
// 32 stride u32
// 36 fourcc u32
// 40 data_len u32
// 44 crc32 u32
// 48 reserved [u32; 8]  (32 bytes)
// 80 payload...
const HEADER_SIZE: usize = 80;
const CRC_OFFSET: usize = 44;

fn now_ns() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as u64)
        .unwrap_or(0)
}

fn region_path(name: &str) -> PathBuf {
    PathBuf::from(format!("/tmp/rhea_{}.shm", name))
}

fn crc32_for_frame(
    magic: u32,
    version: u16,
    state: u16,
    seq: u64,
    timestamp_ns: u64,
    width: u32,
    height: u32,
    stride: u32,
    fourcc: u32,
    data_len: u32,
    reserved: &[u32; 8],
    payload: &[u8],
) -> u32 {
    let mut h = Hasher::new();
    h.update(&magic.to_le_bytes());
    h.update(&version.to_le_bytes());
    h.update(&state.to_le_bytes());
    h.update(&seq.to_le_bytes());
    h.update(&timestamp_ns.to_le_bytes());
    h.update(&width.to_le_bytes());
    h.update(&height.to_le_bytes());
    h.update(&stride.to_le_bytes());
    h.update(&fourcc.to_le_bytes());
    h.update(&data_len.to_le_bytes());
    for x in reserved.iter() {
        h.update(&x.to_le_bytes());
    }
    // crc field treated as zero (do not feed)
    h.update(payload);
    h.finalize()
}

fn write_u16(map: &mut [u8], off: usize, v: u16) {
    map[off..off + 2].copy_from_slice(&v.to_le_bytes());
}
fn write_u32(map: &mut [u8], off: usize, v: u32) {
    map[off..off + 4].copy_from_slice(&v.to_le_bytes());
}
fn write_u64(map: &mut [u8], off: usize, v: u64) {
    map[off..off + 8].copy_from_slice(&v.to_le_bytes());
}
fn read_u16(map: &[u8], off: usize) -> u16 {
    u16::from_le_bytes(map[off..off + 2].try_into().unwrap())
}
fn read_u32(map: &[u8], off: usize) -> u32 {
    u32::from_le_bytes(map[off..off + 4].try_into().unwrap())
}
fn read_u64(map: &[u8], off: usize) -> u64 {
    u64::from_le_bytes(map[off..off + 8].try_into().unwrap())
}
fn read_reserved(map: &[u8]) -> [u32; 8] {
    let mut r = [0u32; 8];
    let mut off = 48usize;
    for i in 0..8 {
        r[i] = read_u32(map, off);
        off += 4;
    }
    r
}
fn write_reserved_zero(map: &mut [u8]) {
    map[48..80].fill(0);
}

pub struct ShmFrameWriter {
    map: MmapMut,
    _file: File,
    capacity: usize,
}

pub struct ShmFrameReader {
    map: MmapMut,
    _file: File,
    capacity: usize,
}

impl ShmFrameWriter {
    #[cfg(target_os = "windows")]
    pub fn create(_name: &str, _capacity: usize) -> Result<Self> {
        bail!("windows not implemented yet")
    }

    #[cfg(not(target_os = "windows"))]
    pub fn create(name: &str, capacity: usize) -> Result<Self> {
        ensure!(!name.is_empty(), "name must not be empty");
        ensure!(capacity > 0, "capacity must be > 0");

        let path = region_path(name);
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(true)
            .open(&path)
            .with_context(|| format!("open shm file {}", path.display()))?;

        file.set_len((HEADER_SIZE + capacity) as u64)?;

        let mut map = unsafe { MmapMut::map_mut(&file)? };
        map[0..HEADER_SIZE].fill(0);

        // init fixed fields
        write_u32(&mut map, 0, MAGIC);
        write_u16(&mut map, 4, VERSION);
        write_u16(&mut map, 6, STATE_EMPTY);
        write_u64(&mut map, 8, 0);
        write_reserved_zero(&mut map);

        Ok(Self {
            map,
            _file: file,
            capacity,
        })
    }

    pub fn write(&mut self, frame: &VideoFrame) -> Result<()> {
        frame.validate()?;
        let data_len = frame.data.len();
        ensure!(data_len <= self.capacity, "frame too large for shm capacity");

        let map = &mut self.map;

        // Atomics are stored in-place at fixed offsets.
        let state_ptr = unsafe { map.as_mut_ptr().add(6) as *mut AtomicU16 };
        let seq_ptr = unsafe { map.as_mut_ptr().add(8) as *mut AtomicU64 };

        // writing
        unsafe { (&*state_ptr).store(STATE_WRITING, Ordering::Release) };

        let seq = unsafe { (&*seq_ptr).fetch_add(1, Ordering::Relaxed) + 1 };

        let ts = now_ns();
        let fourcc_u32 = frame.fourcc.as_u32();
        let reserved = [0u32; 8];

        // fill header (except crc)
        write_u32(map, 0, MAGIC);
        write_u16(map, 4, VERSION);
        write_u64(map, 16, ts);
        write_u32(map, 24, frame.width);
        write_u32(map, 28, frame.height);
        write_u32(map, 32, frame.stride);
        write_u32(map, 36, fourcc_u32);
        write_u32(map, 40, data_len as u32);
        write_u32(map, CRC_OFFSET, 0);
        write_reserved_zero(map);

        // payload
        let payload_off = HEADER_SIZE;
        map[payload_off..payload_off + data_len].copy_from_slice(&frame.data);

        // compute crc deterministically
        let crc = crc32_for_frame(
            MAGIC,
            VERSION,
            STATE_READY,
            seq,
            ts,
            frame.width,
            frame.height,
            frame.stride,
            fourcc_u32,
            data_len as u32,
            &reserved,
            &map[payload_off..payload_off + data_len],
        );
        write_u32(map, CRC_OFFSET, crc);

        // publish seq and ready
        write_u64(map, 8, seq);
        unsafe { (&*state_ptr).store(STATE_READY, Ordering::Release) };

        Ok(())
    }
}

impl ShmFrameReader {
    #[cfg(target_os = "windows")]
    pub fn open(_name: &str) -> Result<Self> {
        bail!("windows not implemented yet")
    }

    #[cfg(not(target_os = "windows"))]
    pub fn open(name: &str) -> Result<Self> {
        ensure!(!name.is_empty(), "name must not be empty");

        let path = region_path(name);
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .open(&path)
            .with_context(|| format!("open shm file {}", path.display()))?;

        let len = file.metadata()?.len() as usize;
        ensure!(len >= HEADER_SIZE, "shm file too small");
        let capacity = len - HEADER_SIZE;

        let map = unsafe { MmapMut::map_mut(&file)? };

        Ok(Self {
            map,
            _file: file,
            capacity,
        })
    }

    pub fn read(&mut self) -> Result<Option<VideoFrame>> {
        let map = &mut self.map;

        let state_ptr = unsafe { map.as_mut_ptr().add(6) as *mut AtomicU16 };
        let seq_ptr = unsafe { map.as_mut_ptr().add(8) as *mut AtomicU64 };

        let state = unsafe { (&*state_ptr).load(Ordering::Acquire) };
        if state != STATE_READY {
            return Ok(None);
        }

        let seq = unsafe { (&*seq_ptr).load(Ordering::Acquire) };

        // snapshot header fields
        let magic = read_u32(map, 0);
        let version = read_u16(map, 4);
        let ts = read_u64(map, 16);
        let width = read_u32(map, 24);
        let height = read_u32(map, 28);
        let stride = read_u32(map, 32);
        let fourcc = read_u32(map, 36);
        let data_len = read_u32(map, 40) as usize;
        let crc = read_u32(map, CRC_OFFSET);
        let reserved = read_reserved(map);

        ensure!(magic == MAGIC, "bad magic");
        ensure!(version == VERSION, "bad version");
        ensure!(data_len <= self.capacity, "data_len exceeds capacity");

        let payload_off = HEADER_SIZE;
        let payload = &map[payload_off..payload_off + data_len];

        let expected = crc32_for_frame(
            magic,
            version,
            STATE_READY,
            seq,
            ts,
            width,
            height,
            stride,
            fourcc,
            data_len as u32,
            &reserved,
            payload,
        );

        if expected != crc {
            return Err(anyhow!("crc mismatch: expected {expected:#x} got {crc:#x}"));
        }

        let frame = VideoFrame {
            width,
            height,
            stride,
            fourcc: FourCC::from_u32(fourcc)?,
            data: payload.to_vec(),
        };

        // consume
        unsafe { (&*state_ptr).store(STATE_EMPTY, Ordering::Release) };

        Ok(Some(frame))
    }
}
