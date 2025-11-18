# Implementation Notes

## Python TPM Wrapper Service

This is a Python port of the C# TPM Wrapper Service, designed to work cross-platform on Windows (x86_64, ARM64) and Linux (x86_64, ARM64).

## Key Differences from C# Version

### 1. TPM Library
- **C#**: Uses `TSS.Net` (Microsoft.TSS) with `TbsDevice` (Windows-only)
- **Python**: Uses `pytss` or `tpm2-pytss` (cross-platform)
  - Works on both Windows and Linux
  - Supports ARM64 and x86_64

### 2. IPC Mechanism
- **C#**: Windows Named Pipes only
- **Python**: 
  - Windows: Named Pipes (via `pywin32`)
  - Linux: Unix Domain Sockets

### 3. Service Architecture
- **C#**: Windows Service (ServiceBase)
- **Python**: Regular process (can be wrapped in systemd/service manager)

### 4. Logging
- **C#**: Windows Event Log
- **Python**: Standard logging (console + file)

## API Compatibility

The Python version maintains the same JSON command protocol:

### Commands

1. **getEK**
   ```json
   {"command": "getEK"}
   ```
   Returns: `ek_public` (base64 X.509), `ek_cert` (base64 DER)

2. **getAttestationData**
   ```json
   {"command": "getAttestationData"}
   ```
   Returns: `ek_pub`, `ek_cert`, `aik_name`

3. **activateCredential**
   ```json
   {
     "command": "activateCredential",
     "credential_blob": "...",
     "encrypted_secret": "...",
     "hmac": "...",
     "enc": "..."
   }
   ```
   Returns: `decrypted_secret` (base64)

## pytss API Notes

The `tpm_manager.py` file uses a simplified pytss API. The actual API may vary depending on the pytss version. You may need to adjust:

1. **Context Creation**: 
   - Current: `ESYS.ESYS_CONTEXT()` then `ctx.connect()`
   - May need: `ESYS.Context()` or different initialization

2. **TPM Commands**:
   - Current: `ctx.ReadPublic()`, `ctx.CreatePrimary()`, etc.
   - May need: Different method names or parameter structures

3. **Handle Types**:
   - Current: `ESYS.ESYS_TR.ENDORSEMENT`
   - May need: `ESYS_TR.ENDORSEMENT` or different constants

## Testing

### Windows
```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python -m tpm_wrapper_service.service
```

### Linux
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure TPM device is accessible
sudo chmod 666 /dev/tpm0  # or /dev/tpmrm0

# Run service
python -m tpm_wrapper_service.service
```

## Known Issues / TODO

1. **pytss API**: The TPM operations in `tpm_manager.py` may need adjustment based on the actual pytss API. Refer to pytss documentation for correct usage.

2. **Windows Named Pipes**: The async implementation may need refinement for better error handling.

3. **Credential Blob Parsing**: The `activateCredential` implementation simplifies the IdObject parsing. Full implementation should properly parse TPM2B_ID_OBJECT structure.

4. **Security**: 
   - Named pipe/socket permissions are set to allow all users (0o666). Should be restricted in production.
   - No authentication at protocol level.

5. **Error Handling**: Some error cases may need more robust handling.

## Architecture Support Matrix

| Platform | Architecture | Status | Notes |
|----------|-------------|--------|-------|
| Windows | x86_64 | ✅ | Requires pywin32 |
| Windows | ARM64 | ✅ | Requires pywin32 |
| Linux | x86_64 | ✅ | Requires TPM device access |
| Linux | ARM64 | ✅ | Requires TPM device access |

## Dependencies

- **pytss** or **tpm2-pytss**: TPM 2.0 library
- **cryptography**: X.509 certificate handling
- **pywin32** (Windows only): Named pipe support
- **Python 3.8+**: Required

