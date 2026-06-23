#!/usr/bin/env python3
"""Generate a synthetic PE-like sample for static analysis demo. NOT real malware."""

import struct
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "synthetic-rust-demo.bin")

STRINGS = [
    b"called `Option::unwrap()` on a `None` value",
    b"std::net::TcpStream",
    b"core::ptr::drop_in_place",
    b"tokio::runtime::Runtime",
    b"https://c2.example.invalid/beacon",
    b"IsDebuggerPresent",
    b"CreateRemoteThread",
    b"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
    b"RUST_BACKTRACE=1",
    b"__rust_eh_personality",
    b"/tmp/.cache_update",
    b"password_token_vault",
]

def build():
    # Minimal PE layout: headers + one .data section containing strings
    dos = bytearray(128)
    dos[0:2] = b"MZ"
    pe_offset = 0x80
    struct.pack_into("<I", dos, 0x3C, pe_offset)

    pe = bytearray()
    pe += b"PE\x00\x00"
    pe += struct.pack("<H", 0x8664)          # Machine AMD64
    pe += struct.pack("<H", 1)                # NumberOfSections
    pe += struct.pack("<I", 0)                # TimeDateStamp
    pe += struct.pack("<I", 0)                # PointerToSymbolTable
    pe += struct.pack("<I", 0)                # NumberOfSymbols
    pe += struct.pack("<H", 240)              # SizeOfOptionalHeader
    pe += struct.pack("<H", 0x22)              # Characteristics

    # Optional header PE32+
    opt = bytearray(240)
    struct.pack_into("<H", opt, 0, 0x20B)     # Magic
    struct.pack_into("<I", opt, 16, 0x1000)   # AddressOfEntryPoint
    struct.pack_into("<Q", opt, 24, 0x10000)  # ImageBase
    struct.pack_into("<I", opt, 32, 0x1000)   # SectionAlignment
    struct.pack_into("<I", opt, 36, 0x200)    # FileAlignment
    struct.pack_into("<I", opt, 56, 0x3000)   # SizeOfImage
    struct.pack_into("<I", opt, 60, 0x200)    # SizeOfHeaders

    section_data = b"\x00" * 512
    for s in STRINGS:
        section_data += s + b"\x00"

    raw_size = len(section_data)
    while len(section_data) % 0x200:
        section_data += b"\x00"

    section = bytearray(40)
    section[0:8] = b".data\x00\x00\x00"
    struct.pack_into("<I", section, 8, raw_size)       # VirtualSize
    struct.pack_into("<I", section, 12, 0x2000)        # VirtualAddress
    struct.pack_into("<I", section, 16, len(section_data))
    struct.pack_into("<I", section, 20, 0x400)          # PointerToRawData
    struct.pack_into("<I", section, 36, 0xC0000040)    # READ|WRITE|INITIALIZED_DATA

    headers = dos + pe + opt + section
    while len(headers) < 0x400:
        headers += b"\x00"

    blob = headers + section_data

    with open(OUTPUT, "wb") as f:
        f.write(blob)

    print(f"Wrote {OUTPUT} ({len(blob)} bytes)")

if __name__ == "__main__":
    build()
