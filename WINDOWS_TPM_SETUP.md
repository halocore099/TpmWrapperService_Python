# Windows TPM 2.0 Library Setup Guide

## The Challenge

`tpm2-pytss` requires:
1. **pkg-config** (Unix tool, not native to Windows)
2. **TSS2 libraries** (tss2-esys, tss2-mu, etc.)
3. **C compiler** (Visual C++ Build Tools)

## Solution Options

### Option 1: MSYS2 (Recommended for Windows)

MSYS2 provides a Unix-like environment on Windows with pkg-config and package management.

#### Step 1: Install MSYS2
1. Download from: https://www.msys2.org/
2. Install to default location: `C:\msys64`
3. After installation, open **MSYS2 UCRT64** terminal (not regular MSYS2)

#### Step 2: Install TSS2 Libraries in MSYS2
```bash
# Update package database
pacman -Syu

# Install TSS2 libraries and build tools
pacman -S mingw-w64-ucrt-x86_64-tpm2-tss
pacman -S mingw-w64-ucrt-x86_64-pkg-config
pacman -S mingw-w64-ucrt-x86_64-gcc
pacman -S mingw-w64-ucrt-x86_64-python
```

#### Step 3: Install tpm2-pytss in MSYS2 Python
```bash
# Use MSYS2's Python
python -m pip install tpm2-pytss
```

**Note**: This installs tpm2-pytss in MSYS2's Python, not your Windows Python. You may need to use MSYS2's Python environment.

### Option 2: Use vcpkg (Alternative)

If you have vcpkg installed:

```powershell
# Install TSS2 libraries via vcpkg
vcpkg install tpm2-tss:x64-windows

# Then set environment variables and install tpm2-pytss
# (This is more complex and requires vcpkg setup)
```

### Option 3: Install Visual C++ Build Tools + Manual TSS2 Build

1. Install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Build TSS2 libraries from source
3. Install pkg-config for Windows
4. Build tpm2-pytss

This is the most complex option.

### Option 4: Use WSL2 (Linux Environment on Windows)

If you have WSL2:
1. Install TSS2 libraries in WSL2 (Ubuntu/Debian)
2. Install tpm2-pytss in WSL2 Python
3. Run the service from WSL2

**Note**: WSL2 can access Windows TPM through `/dev/tpm0` passthrough (if configured).

## Quick Check: Do You Have MSYS2?

Run this in PowerShell:
```powershell
Test-Path "C:\msys64"
```

If it returns `True`, MSYS2 is installed and we can proceed with Option 1.

## Recommended Next Steps

1. **If MSYS2 is installed**: We can set it up to build tpm2-pytss
2. **If not**: Install MSYS2 (Option 1) or use WSL2 (Option 4)
3. **Alternative**: We can create a mock/stub version for testing IPC without real TPM

## Current Status

- ✅ Virtual environment ready
- ✅ Python dependencies installed
- ⚠️ TPM library (tpm2-pytss) needs TSS2 libraries and pkg-config
- ⏳ Waiting for TSS2 library installation method

