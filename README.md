# TPM Wrapper Service (Python)

Cross-platform TPM 2.0 wrapper service supporting Windows (x86_64, ARM64) and Linux.

## Features

- Endorsement Key (EK) management
- Attestation Identity Key (AIK) creation
- Credential activation
- Cross-platform IPC (Named Pipes on Windows, Unix Domain Sockets on Linux)

## Installation

### Quick Install (Recommended)

```bash
# Create virtual environment (recommended, especially on Arch Linux)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Note:** On Arch Linux, you may see "externally managed" - use venv as shown above.

### TPM Library

The service uses `tpm2-pytss` which is **bundled with the package**. All required TSS2 libraries (DLLs on Windows, .so files on Linux) are included, so no additional installation is needed.

**For developers building from source:** See [BUILD.md](BUILD.md) for instructions on building with bundled libraries.

For detailed installation instructions, including troubleshooting, see [INSTALLATION.md](INSTALLATION.md).

## Running

### Linux (as daemon)
```bash
python -m tpm_wrapper_service.service
```

### Windows (as service)
```bash
python -m tpm_wrapper_service.service
```

## Usage

### Running the Service

```bash
# Start the TPM wrapper service
python -m tpm_wrapper_service.service
```

### Registering with a Server

If you have a server that accepts TPM registration:

```bash
# Register with server (replace with your server URL)
python tpm_client.py http://your-server-ip:port

# Or the script will prompt for server URL
python tpm_client.py
```

The client will:
1. Get attestation data from TPM service
2. Register with the server
3. Receive a challenge
4. Activate the credential using TPM
5. Complete the challenge

## Testing

### Quick Test (All Features)
Run the comprehensive test script to test all features:

```bash
# Make sure the service is running first
python -m tpm_wrapper_service.service

# In another terminal, run the test script
python test_all_features.py
```

The test script will:
- Test all three commands (getEK, getAttestationData, activateCredential)
- Test error handling
- Generate a detailed report
- Work on both Linux and Windows
- Save results to a JSON file

## Architecture Support

- Windows x86_64
- Windows ARM64
- Linux x86_64
- Linux ARM64

## Documentation

Additional documentation is available in the `markdown/` directory:

- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation guide and troubleshooting
- **[ARCHITECTURE.md](markdown/ARCHITECTURE.md)** - Architecture support details
- **[COMPARISON.md](markdown/COMPARISON.md)** - Detailed C# to Python comparison
- **[SIMPLE_EXPLANATION.md](markdown/SIMPLE_EXPLANATION.md)** - Simple explanation of how it works
- **[NOT_PORTED.md](markdown/NOT_PORTED.md)** - What wasn't ported and why
- **[TESTING.md](markdown/TESTING.md)** - Testing guide
- **[TPM_TESTING_OPTIONS.md](markdown/TPM_TESTING_OPTIONS.md)** - Testing with fTPM and WSL
- **[IMPLEMENTATION_NOTES.md](markdown/IMPLEMENTATION_NOTES.md)** - Implementation details and notes

