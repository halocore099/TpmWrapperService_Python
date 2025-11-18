# Building TPM Wrapper Service with Bundled Libraries

This guide explains how to build the TPM Wrapper Service with bundled tpm2-pytss and TSS2 libraries for easy distribution.

## Overview

The build process:
1. Builds tpm2-pytss in MSYS2 (Windows) or native Linux environment
2. Extracts required TSS2 libraries (DLLs on Windows, .so files on Linux)
3. Bundles them with the Python package
4. Creates platform-specific wheels

## Prerequisites

### Windows
- MSYS2 installed (https://www.msys2.org/)
- Python 3.8+ (Windows Python, not MSYS2 Python for final wheel)
- Virtual environment (recommended)

### Linux
- TSS2 development libraries installed
- Python 3.8+
- Build tools (gcc, pkg-config, etc.)
- Virtual environment (recommended)

## Quick Build

### Windows

```powershell
# Run the build script
.\build_windows.ps1
```

The script will:
1. Guide you through MSYS2 setup
2. Extract DLLs from MSYS2
3. Build the Windows wheel

### Linux

```bash
# Make script executable
chmod +x build_linux.sh

# Run the build script
./build_linux.sh
```

The script will:
1. Check for TSS2 libraries
2. Build tpm2-pytss if needed
3. Extract .so files
4. Build the Linux wheel

## Detailed Build Instructions

### Windows (MSYS2)

#### Step 1: Install MSYS2

1. Download from https://www.msys2.org/
2. Install to default location: `C:\msys64`
3. Open **MSYS2 UCRT64** terminal (not regular MSYS2)

#### Step 2: Install TSS2 Libraries and Build Tools

In MSYS2 UCRT64 terminal:

```bash
# Update package database
pacman -Syu

# Install TSS2 libraries
pacman -S mingw-w64-ucrt-x86_64-tpm2-tss

# Install build tools
pacman -S mingw-w64-ucrt-x86_64-pkg-config mingw-w64-ucrt-x86_64-gcc

# Install Python
pacman -S mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-pip
```

#### Step 3: Build tpm2-pytss

In MSYS2 UCRT64 terminal:

```bash
python -m pip install tpm2-pytss
python -c "import tpm2_pytss; print('OK')"
```

#### Step 4: Extract DLLs

Run the build script from Windows PowerShell:

```powershell
.\build_windows.ps1
```

Or manually copy DLLs:

```powershell
# Copy from MSYS2 to project
Copy-Item "C:\msys64\ucrt64\bin\tss2*.dll" -Destination "tpm_wrapper_service\libs\windows\"
```

#### Step 5: Build Wheel

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Build wheel
python setup.py bdist_wheel
```

### Linux (Ubuntu/Debian)

#### Step 1: Install TSS2 Libraries

```bash
sudo apt-get update
sudo apt-get install -y libtss2-dev tpm2-tools pkg-config python3-dev python3-pip build-essential
```

#### Step 2: Build tpm2-pytss

```bash
python3 -m pip install tpm2-pytss
python3 -c "import tpm2_pytss; print('OK')"
```

#### Step 3: Extract Libraries

Run the build script:

```bash
chmod +x build_linux.sh
./build_linux.sh
```

Or manually:

```bash
# Find libraries
find /usr -name "libtss2*.so*" 2>/dev/null

# Copy to project (adjust paths as needed)
cp /usr/lib/x86_64-linux-gnu/libtss2*.so* tpm_wrapper_service/libs/linux/x86_64/
```

#### Step 4: Build Wheel

```bash
python3 setup.py bdist_wheel
```

### Linux (Arch)

#### Step 1: Install TSS2 Libraries

```bash
sudo pacman -S tpm2-tss tpm2-tools python python-pip base-devel
```

#### Step 2-4: Same as Ubuntu/Debian

Follow steps 2-4 from the Ubuntu/Debian section above.

## Building for Multiple Platforms

### Using WSL2

If you have WSL2 with Ubuntu, you can build both platforms:

1. Build Windows wheel on Windows (using MSYS2)
2. Build Linux wheel in WSL2 (using native Linux tools)

The wheels will be in the `dist/` directory.

## Verifying the Build

### Check Wheel Contents

**Windows:**
```powershell
# List contents
python -m zipfile -l dist\tpm_wrapper_service-*-win_amd64.whl | Select-String "libs/windows"
```

**Linux:**
```bash
# List contents
unzip -l dist/tpm_wrapper_service-*-linux_x86_64.whl | grep "libs/linux"
```

### Test Installation

**Windows:**
```powershell
# Create fresh venv
python -m venv test_venv
.\test_venv\Scripts\Activate.ps1

# Install wheel
pip install dist\tpm_wrapper_service-*-win_amd64.whl

# Test import
python -c "from tpm_wrapper_service import service; print('OK')"
```

**Linux:**
```bash
# Create fresh venv
python3 -m venv test_venv
source test_venv/bin/activate

# Install wheel
pip install dist/tpm_wrapper_service-*-linux_x86_64.whl

# Test import
python3 -c "from tpm_wrapper_service import service; print('OK')"
```

## Troubleshooting

### Windows: DLLs Not Found

- Verify MSYS2 is installed at `C:\msys64`
- Check that tpm2-pytss is installed in MSYS2 Python
- Verify DLLs exist in `C:\msys64\ucrt64\bin\`

### Linux: Libraries Not Found

- Install TSS2 development libraries: `libtss2-dev` (Ubuntu) or `tpm2-tss` (Arch)
- Check library paths: `find /usr -name "libtss2*.so*"`
- Verify pkg-config: `pkg-config --exists tss2-esys`

### Wheel Missing Libraries

- Check `MANIFEST.in` includes library patterns
- Verify `setup.py` has `include_package_data=True`
- Check `package_data` includes correct paths

### Import Errors After Installation

- Verify library loader is called before TSS imports
- Check `lib_loader.py` is in the package
- Verify libraries are in the correct directory structure

## Library Structure

The bundled libraries are organized as:

```
tpm_wrapper_service/
  libs/
    windows/
      tss2-esys.dll
      tss2-mu.dll
      tss2-rcdecode.dll
      tss2-tctildr.dll
      tss2-tcti-tbs.dll
    linux/
      x86_64/
        libtss2-esys.so*
        libtss2-mu.so*
        libtss2-rcdecode.so*
        libtss2-tctildr.so*
        libtss2-tcti-device.so*
      aarch64/
        (for ARM64 Linux - future)
```

## Cross-Platform Compatibility

- **Windows wheels** work on all Windows versions (10, 11, Server)
- **Linux wheels** are distribution-agnostic (same wheel works on Ubuntu, Arch, Debian, Fedora, etc.)
- Libraries are ABI-compatible across distributions for the same architecture

## Next Steps

After building:
1. Test the wheel on a clean system
2. Verify TPM operations work (if TPM available)
3. Distribute the wheel to users
4. Users can install with: `pip install tpm_wrapper_service-*.whl`

