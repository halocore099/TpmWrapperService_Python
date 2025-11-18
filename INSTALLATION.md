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

## TPM Library Options

### Option 1: pytss (Recommended) ✅

**Works out of the box:**
```bash
pip install pytss
```

This installs `pytss` version 0.1.4 (or latest available), which works perfectly with this service.

### Option 2: tpm2-pytss (Alternative)

**Requires build dependencies on Linux:**

#### Arch Linux
```bash
# Install build dependencies
sudo pacman -S tpm2-tss tpm2-tools python-setuptools python-wheel

# Then install tpm2-pytss
pip install tpm2-pytss
```

#### Ubuntu/Debian
```bash
# Install build dependencies
sudo apt-get install libtss2-dev tpm2-tools python3-dev build-essential

# Then install tpm2-pytss
pip install tpm2-pytss
```

#### Fedora
```bash
# Install build dependencies
sudo dnf install tpm2-tss-devel tpm2-tools python3-devel gcc

# Then install tpm2-pytss
pip install tpm2-pytss
```

**Note:** You only need ONE of these libraries. `pytss` is recommended as it's easier to install.

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
# Test pytss import
python -c "from TSS import ESYS; print('pytss works!')"

# Test service start (will fail if TPM not accessible, but should import)
python -c "from tpm_wrapper_service import service; print('Service module loads!')"
```

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

