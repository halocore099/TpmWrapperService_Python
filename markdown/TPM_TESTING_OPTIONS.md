# TPM Testing Options: fTPM and WSL

This document explains testing options including fTPM (firmware TPM) and WSL (Windows Subsystem for Linux).

---

## fTPM (Firmware TPM) ✅ **YES, WORKS**

### What is fTPM?
- **fTPM** = Firmware TPM
- Software-based TPM implementation running in firmware (UEFI/BIOS)
- TPM 2.0 compliant
- Common on modern systems (especially laptops)

### Can you test with fTPM?
**Yes!** fTPM works perfectly with this service.

### Why it works:
- fTPM is a **real TPM 2.0 implementation**
- It exposes the same TPM 2.0 interface
- `pytss` and TPM libraries work with it just like discrete TPM chips
- Windows TBS (TPM Base Services) supports fTPM
- Linux TPM device drivers support fTPM

### How to check if you have fTPM:

**Windows:**
```powershell
# Check TPM status
Get-Tpm

# Or use TPM Management console
tpm.msc
```

**Linux:**
```bash
# Check if TPM device exists
ls -l /dev/tpm*

# Check TPM info
tpm2_getcap properties-variable

# Or check dmesg for TPM
dmesg | grep -i tpm
```

### Testing with fTPM:
- **No special configuration needed**
- Works exactly like a discrete TPM chip
- All TPM operations work normally
- Same commands, same responses

**Example:**
```bash
# Just run the service normally
python -m tpm_wrapper_service.service

# fTPM will be used automatically if it's the only TPM available
```

---

## WSL (Windows Subsystem for Linux) ⚠️ **PROBLEMATIC**

### What is WSL?
- **WSL** = Windows Subsystem for Linux
- Runs Linux in user mode on Windows
- WSL2 uses a real Linux kernel (virtualized)
- WSL1 uses a translation layer

### Can you test Linux part with WSL?
**Partially, but with limitations.**

### The Problem: TPM Device Access

#### Issue 1: Device File Access
- Linux TPM access requires `/dev/tpm0` or `/dev/tpmrm0`
- WSL may not have direct access to host TPM device files
- Even if device files exist, they might not connect to the actual TPM

#### Issue 2: TPM Passthrough
- WSL doesn't natively pass through TPM devices
- The Linux kernel in WSL doesn't have direct hardware access
- TPM device would need to be explicitly passed through (not standard)

#### Issue 3: Windows TPM vs Linux TPM
- WSL would be trying to access the **Windows TPM** (fTPM or discrete)
- But through Linux device files, not Windows TBS
- This creates a mismatch

### What WILL Work in WSL:
✅ **IPC Server (Unix Sockets)**
- Unix domain sockets work fine in WSL
- The communication mechanism will work
- You can test the IPC protocol

✅ **Code Execution**
- Python code runs fine
- Libraries install normally
- Service starts and runs

❌ **TPM Operations**
- TPM device access likely won't work
- `/dev/tpm0` may not exist or may not connect to real TPM
- TPM commands will fail

### Testing Strategy for WSL:

#### Option 1: Mock TPM Operations
```python
# Test IPC and protocol without real TPM
# Use mocks for TPM operations
# Verify JSON protocol works
```

#### Option 2: Test IPC Only
```python
# Test that Unix sockets work
# Test message parsing
# Test command handling (with mocked TPM responses)
```

#### Option 3: Use Windows TPM from WSL (Advanced)
- This would require custom bridging
- Not recommended - too complex
- Better to use actual Linux

### Better Alternatives for Linux Testing:

#### Option 1: Native Linux Machine
- **Best option**: Real Linux system
- Full TPM access
- Native device files
- Real-world testing

#### Option 2: Linux VM with TPM Passthrough
- VirtualBox/VMware with TPM passthrough
- Full Linux environment
- Access to host TPM
- More realistic than WSL

#### Option 3: Cloud Linux Instance
- AWS/GCP/Azure Linux VM
- May have vTPM (virtual TPM)
- Good for integration testing

---

## Testing Matrix

| Environment | TPM Access | IPC Works | Full Testing |
|------------|------------|-----------|--------------|
| **Windows (Native)** | ✅ Yes (TBS) | ✅ Yes (Named Pipes) | ✅ Full |
| **Linux (Native)** | ✅ Yes (/dev/tpm0) | ✅ Yes (Unix Sockets) | ✅ Full |
| **fTPM (Windows)** | ✅ Yes (via TBS) | ✅ Yes | ✅ Full |
| **fTPM (Linux)** | ✅ Yes (via /dev/tpm0) | ✅ Yes | ✅ Full |
| **WSL** | ❌ No (no device access) | ✅ Yes (Unix Sockets) | ⚠️ Partial (IPC only) |
| **Linux VM** | ⚠️ Maybe (if passthrough) | ✅ Yes | ⚠️ Depends |

---

## Recommended Testing Approach

### For Windows Testing:
1. ✅ Use fTPM or discrete TPM (both work)
2. ✅ Test with native Windows
3. ✅ Test Named Pipes IPC

### For Linux Testing:
1. ✅ **Best**: Native Linux machine
2. ✅ **Good**: Linux VM with TPM passthrough
3. ⚠️ **Limited**: WSL (IPC only, no TPM)

### For Cross-Platform Testing:
1. ✅ Test Windows on Windows machine
2. ✅ Test Linux on Linux machine
3. ⚠️ WSL can test Linux IPC code, but not TPM operations

---

## How to Test IPC in WSL (Without TPM)

If you want to test the Linux IPC mechanism in WSL:

```python
# test_ipc_wsl.py
# Mock the TPM operations, test IPC only

from unittest.mock import Mock, patch
from tpm_wrapper_service import ipc_server

# Mock TPM context
mock_tpm = Mock()

# Create IPC server with mock
server = ipc_server.IPCServer(mock_tpm)

# Test that Unix socket creation works
# Test that message parsing works
# Test that JSON protocol works
```

This lets you verify:
- ✅ Unix socket creation
- ✅ Message parsing
- ✅ JSON protocol
- ✅ Command routing
- ❌ Actual TPM operations (mocked)

---

## Summary

### fTPM: ✅ **YES, USE IT**
- Works perfectly
- No special configuration
- Same as discrete TPM for testing purposes
- Great for development and testing

### WSL: ⚠️ **LIMITED USE**
- ✅ Good for testing IPC/protocol
- ✅ Good for testing code execution
- ❌ **Cannot test actual TPM operations**
- ❌ No access to `/dev/tpm0` that connects to real TPM
- ⚠️ Better to use real Linux or VM for full testing

### Recommendation:
- **Windows testing**: Use fTPM or discrete TPM on Windows
- **Linux testing**: Use real Linux machine or VM with TPM passthrough
- **WSL**: Only for IPC/protocol testing, not TPM operations

---

## Quick Check Commands

### Check if fTPM is available (Windows):
```powershell
Get-Tpm | Select-Object TpmPresent, TpmReady, ManufacturerVersionInfo
```

### Check if TPM device exists (WSL/Linux):
```bash
# In WSL - likely won't exist or won't work
ls -l /dev/tpm*

# Check if it's accessible
sudo tpm2_getcap properties-variable 2>&1
```

### Test if TPM works (Windows):
```powershell
# Should show TPM info
Get-Tpm
```

### Test if TPM works (Linux):
```bash
# Should show TPM info
tpm2_getcap properties-variable
```

If these commands work, TPM is accessible. If they fail, TPM access isn't available in that environment.

