# Installation Guide

## Quick Start

### Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## TPM Library

### Bundled tpm2-pytss (Default) ✅

**The package includes bundled tpm2-pytss and all required TSS2 libraries.**

When you install the package from a wheel, all TSS2 libraries (DLLs on Windows, .so files on Linux) are automatically included. **No additional installation is needed.**

**Benefits:**
- No need to install TSS2 libraries separately
- Works on clean systems without build tools
- Cross-platform support (Windows + Linux)
- Distribution-agnostic Linux wheels (works on Ubuntu, Arch, Debian, Fedora, etc.)

**For developers building from source:** See [BUILD.md](BUILD.md) for instructions on building with bundled libraries.

### Legacy Option: pytss (Not Recommended)

The old `pytss` library (TPM 1.2 only) is no longer recommended. The bundled `tpm2-pytss` (TPM 2.0) is the default and preferred option.

## Platform-Specific Requirements

### Linux

#### TPM Access Permissions
```bash
# Add user to tss group (if it exists)
sudo usermod -aG tss $USER

# Log out and back in, or use:
newgrp tss
```

#### Verify TPM Access
```bash
# Check TPM device
ls -l /dev/tpm*

# Test TPM access
tpm2_getcap properties-variable
```

### Windows

#### Dependencies
- `pywin32` is automatically installed when you run `pip install -r requirements.txt` on Windows
- TPM access works via TBS (TPM Base Services) - usually works if running as Administrator

#### Verify TPM
```powershell
# Check TPM status
Get-Tpm
```

## Troubleshooting

### "externally managed" Error (Arch Linux)

This is normal! Use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### tpm2-pytss Build Failures

If `tpm2-pytss` fails to build:
1. **Don't worry** - you don't need it if `pytss` works
2. If you want to use it, install the build dependencies listed above
3. Make sure you have `python-setuptools` and `python-wheel` installed

### TPM Permission Denied

**Linux:**
```bash
# Add to tss group
sudo usermod -aG tss $USER
newgrp tss

# Or check device permissions
ls -l /dev/tpm0
# Should be readable by tss group or your user
```

**Windows:**
- Run as Administrator if TPM access fails

### Module Not Found Errors

Make sure you're in your virtual environment:
```bash
# Check if venv is active (should show (venv) in prompt)
which python  # Should point to venv/bin/python

# If not active:
source venv/bin/activate
```

## Verification

After installation, verify everything works:

```bash
# Test tpm2-pytss import (bundled)
python -c "import tpm2_pytss; print('tpm2-pytss works!')"

# Test service start (will fail if TPM not accessible, but should import)
python -c "from tpm_wrapper_service import service; print('Service module loads!')"
```

**Note:** If you're building from source, ensure you've followed the [BUILD.md](BUILD.md) instructions to bundle the libraries.

## Full Installation Example (Arch Linux)

```bash
# 1. Create and activate venv
python -m venv venv
source venv/bin/activate

# 2. Install pytss (easiest option)
pip install pytss

# 3. Install other dependencies
pip install cryptography pyasn1 pyasn1-modules

# 4. Verify
python -c "from TSS import ESYS; print('Success!')"

# 5. Set up TPM access (if needed)
sudo usermod -aG tss $USER
newgrp tss
```

