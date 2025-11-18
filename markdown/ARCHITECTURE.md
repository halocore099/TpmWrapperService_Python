# Architecture Support

This Python implementation supports the following platforms and architectures:

## Supported Platforms

### Windows
- **x86_64** (64-bit Intel/AMD)
- **ARM64** (64-bit ARM)

### Linux
- **x86_64** (64-bit Intel/AMD)
- **ARM64** (64-bit ARM, including Raspberry Pi 4+)

## Platform-Specific Features

### Windows
- Uses Windows Named Pipes for IPC (`\\.\pipe\TpmWrapperPipe`)
- Requires `pywin32` package
- Uses TBS (TPM Base Services) via pytss

### Linux
- Uses Unix Domain Sockets for IPC (`/tmp/TpmWrapperPipe.sock`)
- Requires TPM device access (`/dev/tpm0` or `/dev/tpmrm0`)
- Uses TPM Resource Manager or direct device access via pytss

## Dependencies

### Core (All Platforms)
- `pytss` or `tpm2-pytss` - TPM 2.0 library
- `cryptography` - Cryptographic operations
- Python 3.8+

### Windows-Specific
- `pywin32` - Windows API access for named pipes

## Installation

### Linux
```bash
pip install -r requirements.txt
```

### Windows
```bash
pip install -r requirements.txt
# pywin32 will be installed automatically on Windows
```

## Running

The service automatically detects the platform and uses the appropriate IPC mechanism:

```bash
python -m tpm_wrapper_service.service
```

## Differences from C# Version

1. **Cross-platform IPC**: Uses Unix sockets on Linux, named pipes on Windows
2. **No Windows Service**: Runs as a regular process (can be wrapped in systemd/service manager)
3. **Python async**: Uses asyncio for concurrent operations
4. **Platform detection**: Automatic platform and architecture detection

