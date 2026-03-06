import subprocess
import struct

def find_pointer_in_section(arch, segment, section, target_addr):
    # Get section info to find offset and size
    cmd = ["otool", "-arch", arch, "-l", "/Applications/Play.app/Contents/MacOS/Play"]
    out = subprocess.check_output(cmd).decode()
    
    found_section = False
    offset = 0
    size = 0
    addr = 0
    
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if f"sectname {section}" in line and f"segname {segment}" in lines[i+1]:
            addr = int(lines[i+2].split()[1], 16)
            size = int(lines[i+3].split()[1], 16)
            offset = int(lines[i+4].split()[1], 16)
            found_section = True
            break
            
    if not found_section:
        return None

    # Read the binary at that offset
    with open("/Applications/Play.app/Contents/MacOS/Play", "rb") as f:
        f.seek(offset)
        data = f.read(size)
        
    # Search for target_addr (8-byte little endian)
    # Target may be tagged or have high bits, so we check the lower 32/48 bits if needed
    # but usually it's a direct pointer in selrefs
    target_bytes = struct.pack("<Q", target_addr)
    
    ptr_size = 8
    for i in range(0, len(data), ptr_size):
        ptr_val = struct.unpack("<Q", data[i:i+ptr_size])[0]
        # Strip potential ARM64 pointer authentication or tags if no direct match
        if ptr_val == target_addr or (ptr_val & 0xFFFFFFFFFF) == (target_addr & 0xFFFFFFFFFF):
            return addr + i
            
    return None

# arm64 METHNAME_ADDR = 0x102ed2b4b
# x86_64 METHNAME_ADDR = 0x103683b85 (from previous turns)

selref_arm64 = find_pointer_in_section("arm64", "__DATA", "__objc_selrefs", 0x102ed2b4b)
print(f"ARM64 SELREF_ADDR: {hex(selref_arm64) if selref_arm64 else 'Not Found'}")

selref_x86_64 = find_pointer_in_section("x86_64", "__DATA", "__objc_selrefs", 0x103683b85)
print(f"X86_64 SELREF_ADDR: {hex(selref_x86_64) if selref_x86_64 else 'Not Found'}")
