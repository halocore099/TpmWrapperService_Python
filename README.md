# TPM Wrapper Service (Python)

Cross-platform TPM 2.0 wrapper service supporting Windows (x86_64, ARM64) and Linux.

## Features

- Endorsement Key (EK) management
- Attestation Identity Key (AIK) creation
- Credential activation
- Cross-platform IPC (Named Pipes on Windows, Unix Domain Sockets on Linux)

## Installation

```bash
pip install -r requirements.txt
```

## Running

### Linux (as daemon)
```bash
python -m tpm_wrapper_service.service
```

### Windows (as service)
```bash
python -m tpm_wrapper_service.service
```

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

- **[ARCHITECTURE.md](markdown/ARCHITECTURE.md)** - Architecture support details
- **[COMPARISON.md](markdown/COMPARISON.md)** - Detailed C# to Python comparison
- **[SIMPLE_EXPLANATION.md](markdown/SIMPLE_EXPLANATION.md)** - Simple explanation of how it works
- **[NOT_PORTED.md](markdown/NOT_PORTED.md)** - What wasn't ported and why
- **[TESTING.md](markdown/TESTING.md)** - Testing guide
- **[TPM_TESTING_OPTIONS.md](markdown/TPM_TESTING_OPTIONS.md)** - Testing with fTPM and WSL
- **[IMPLEMENTATION_NOTES.md](markdown/IMPLEMENTATION_NOTES.md)** - Implementation details and notes

