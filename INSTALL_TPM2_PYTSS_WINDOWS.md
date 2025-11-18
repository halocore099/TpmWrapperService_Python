# Installing tpm2-pytss on Windows - Step by Step

## Overview

To get `tpm2-pytss` working on Windows, we need MSYS2 which provides the Unix tools (pkg-config) and TSS2 libraries needed for building.

## Step-by-Step Installation

### Step 1: Install MSYS2

1. **Download MSYS2**:
   - Go to: https://www.msys2.org/
   - Download the installer (usually `msys2-x86_64-*.exe`)
   - Run the installer and install to `C:\msys64` (default)

2. **After installation**:
   - Close the terminal that opens automatically
   - Open **MSYS2 UCRT64** (not regular MSYS2)
     - You can find it in Start Menu: "MSYS2 UCRT64"
     - Or navigate to `C:\msys64\ucrt64.exe`

### Step 2: Update MSYS2 Packages

In the MSYS2 UCRT64 terminal, run:
```bash
pacman -Syu
```
(You may need to close and reopen the terminal after this)

### Step 3: Install TSS2 Libraries and Build Tools

In MSYS2 UCRT64 terminal:
```bash
pacman -S mingw-w64-ucrt-x86_64-tpm2-tss
pacman -S mingw-w64-ucrt-x86_64-pkg-config
pacman -S mingw-w64-ucrt-x86_64-gcc
pacman -S mingw-w64-ucrt-x86_64-python
pacman -S mingw-w64-ucrt-x86_64-python-pip
```

### Step 4: Install tpm2-pytss

In MSYS2 UCRT64 terminal:
```bash
python -m pip install tpm2-pytss
```

### Step 5: Verify Installation

In MSYS2 UCRT64 terminal:
```bash
python -c "import tpm2_pytss; print('tpm2-pytss installed successfully!')"
```

## Using MSYS2 Python vs Windows Python

**Important**: The above installs tpm2-pytss in MSYS2's Python environment. You have two options:

### Option A: Use MSYS2 Python for the Project
- Run your service from MSYS2 UCRT64 terminal
- Use MSYS2's Python: `python -m tpm_wrapper_service.service`

### Option B: Make tpm2-pytss Available to Windows Python (Advanced)
This requires copying libraries and setting up paths - more complex.

## Alternative: Quick Test with Mock

If you want to test the service without installing all this, we can create a mock version that simulates TPM operations for testing the IPC and protocol.

## Next Steps

Once MSYS2 is installed, let me know and I can help you:
1. Verify the installation
2. Test tpm2-pytss import
3. Run the service
4. Run the test suite

## Estimated Time

- MSYS2 download: 5-10 minutes
- MSYS2 installation: 2-3 minutes
- Package installation: 5-10 minutes
- **Total: ~15-25 minutes**

