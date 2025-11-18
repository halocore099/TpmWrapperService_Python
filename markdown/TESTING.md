# Testing Guide for TPM Wrapper Service

This guide explains how to test the Python TPM Wrapper Service.

---

## Prerequisites

### Hardware Requirements
- **TPM 2.0 chip** (required for actual TPM operations)
  - Most modern computers have TPM 2.0
  - Windows: Check in Device Manager or `tpm.msc`
  - Linux: Check `/dev/tpm0` or `/dev/tpmrm0`

### Software Requirements
- Python 3.8+
- TPM libraries installed:
  ```bash
  pip install -r requirements.txt
  ```
- TPM access permissions:
  - **Windows**: Usually works if running as Administrator
  - **Linux**: May need to add user to `tss` group or use `sudo`

---

## Testing Methods

### 1. Manual Testing (End-to-End)

#### Step 1: Start the Service

**Windows:**
```bash
cd TpmWrapperService_Python
python -m tpm_wrapper_service.service
```

**Linux:**
```bash
cd TpmWrapperService_Python
# May need sudo if TPM device requires root
sudo python -m tpm_wrapper_service.service
# OR add user to tss group first
```

You should see:
```
INFO - Starting TPM Wrapper Service...
INFO - Platform: win32, Architecture: x86_64
INFO - Connected to TPM
INFO - IPC Server started on \\.\pipe\TpmWrapperPipe
INFO - Waiting for client connection...
```

#### Step 2: Test with a Client

Create a simple test client in Python:

**test_client.py:**
```python
import json
import socket
import sys
import platform

def test_windows_named_pipe():
    """Test on Windows using named pipe"""
    import win32pipe
    import win32file
    
    pipe_name = r'\\.\pipe\TpmWrapperPipe'
    
    try:
        # Connect to named pipe
        pipe_handle = win32file.CreateFile(
            pipe_name,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )
        
        # Send command
        command = json.dumps({"command": "getEK"}) + "\n"
        win32file.WriteFile(pipe_handle, command.encode('utf-8'))
        
        # Read response
        result, data = win32file.ReadFile(pipe_handle, 4096)
        response = json.loads(data.decode('utf-8'))
        
        print("Response:", json.dumps(response, indent=2))
        
        win32file.CloseHandle(pipe_handle)
        
    except Exception as e:
        print(f"Error: {e}")

def test_unix_socket():
    """Test on Linux using Unix socket"""
    socket_path = '/tmp/TpmWrapperPipe.sock'
    
    try:
        # Connect to Unix socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_path)
        
        # Send command
        command = json.dumps({"command": "getEK"}) + "\n"
        sock.sendall(command.encode('utf-8'))
        
        # Read response
        response_data = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
            if b'\n' in response_data:
                break
        
        response = json.loads(response_data.decode('utf-8'))
        print("Response:", json.dumps(response, indent=2))
        
        sock.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    if platform.system() == 'Windows':
        test_windows_named_pipe()
    else:
        test_unix_socket()
```

**Run the test:**
```bash
# In a separate terminal
python test_client.py
```

#### Step 3: Test All Commands

**test_all_commands.py:**
```python
import json
import socket
import sys
import platform
import base64

# ... (same connection code as above) ...

def test_get_ek():
    """Test getEK command"""
    command = json.dumps({"command": "getEK"}) + "\n"
    response = send_command(command)
    print("\n=== getEK ===")
    print(json.dumps(response, indent=2))
    assert response['status'] == 'ok'
    assert 'ek_public' in response
    print("✅ getEK test passed")

def test_get_attestation_data():
    """Test getAttestationData command"""
    command = json.dumps({"command": "getAttestationData"}) + "\n"
    response = send_command(command)
    print("\n=== getAttestationData ===")
    print(json.dumps(response, indent=2))
    assert response['status'] == 'ok'
    assert 'ek_pub' in response
    assert 'aik_name' in response
    print("✅ getAttestationData test passed")

def test_activate_credential():
    """Test activateCredential command"""
    # First get attestation data to get AIK name
    attestation = send_command(json.dumps({"command": "getAttestationData"}) + "\n")
    aik_name = attestation['aik_name']
    
    # Note: In real scenario, you'd get credential_blob and encrypted_secret
    # from an attestation server. For testing, you'd need to set up a full
    # attestation flow or use mock data.
    
    command = json.dumps({
        "command": "activateCredential",
        "credential_blob": "base64-encoded-blob",
        "encrypted_secret": "base64-encoded-secret",
        "hmac": "base64-encoded-hmac",
        "enc": "base64-encoded-enc"
    }) + "\n"
    
    response = send_command(command)
    print("\n=== activateCredential ===")
    print(json.dumps(response, indent=2))
    # This will likely fail without real credential data
    print("⚠️  activateCredential requires real attestation server")

if __name__ == '__main__':
    test_get_ek()
    test_get_attestation_data()
    test_activate_credential()
```

---

### 2. Unit Testing

Create unit tests for individual components:

**tests/test_tpm_manager.py:**
```python
import unittest
from unittest.mock import Mock, patch
from tpm_wrapper_service import tpm_manager

class TestTpmManager(unittest.TestCase):
    
    @patch('tpm_wrapper_service.tpm_manager.ESYS')
    def test_load_or_create_ek(self, mock_esys):
        """Test EK loading/creation"""
        # Mock TPM context
        mock_ctx = Mock()
        mock_ctx.ReadPublic.return_value = (Mock(), None, None)
        
        # Test loading existing EK
        ek_handle, ek_public, ek_cert = tpm_manager.load_or_create_ek(mock_ctx)
        
        self.assertIsNotNone(ek_handle)
        self.assertIsNotNone(ek_public)
    
    def test_normalize_modulus(self):
        """Test modulus normalization"""
        # Test with leading zeros
        modulus_with_zeros = bytes([0, 0, 0, 1, 2, 3])
        normalized = tpm_manager.normalize_modulus(modulus_with_zeros)
        
        self.assertEqual(normalized, bytes([1, 2, 3]))
        
        # Test without leading zeros
        modulus_no_zeros = bytes([1, 2, 3])
        normalized = tpm_manager.normalize_modulus(modulus_no_zeros)
        
        self.assertEqual(normalized, bytes([1, 2, 3]))

if __name__ == '__main__':
    unittest.main()
```

**tests/test_ek_exporter.py:**
```python
import unittest
from tpm_wrapper_service import ek_exporter

class TestEkExporter(unittest.TestCase):
    
    def test_export_rsa_ek(self):
        """Test RSA EK export to X.509"""
        # Mock RSA modulus (256 bytes for 2048-bit key)
        modulus = b'\x00' * 255 + b'\x01'  # Dummy modulus
        exponent = 65537
        
        result = ek_exporter.export_rsa_ek_to_base64_x509(modulus, exponent)
        
        # Should return base64 string
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
        # Should be valid base64
        import base64
        try:
            decoded = base64.b64decode(result)
            self.assertGreater(len(decoded), 0)
        except Exception:
            self.fail("Result is not valid base64")

if __name__ == '__main__':
    unittest.main()
```

**tests/test_crypto_lib.py:**
```python
import unittest
from tpm_wrapper_service import crypto_lib

class TestCryptoLib(unittest.TestCase):
    
    def test_random_bytes(self):
        """Test random byte generation"""
        # Test different lengths
        for length in [16, 32, 64, 128]:
            random_data = crypto_lib.random_bytes(length)
            
            self.assertEqual(len(random_data), length)
            self.assertIsInstance(random_data, bytes)
        
        # Test that results are different
        data1 = crypto_lib.random_bytes(32)
        data2 = crypto_lib.random_bytes(32)
        self.assertNotEqual(data1, data2)

if __name__ == '__main__':
    unittest.main()
```

**Run unit tests:**
```bash
python -m pytest tests/
# OR
python -m unittest discover tests
```

---

### 3. Integration Testing

Test the full service with a real TPM:

**tests/test_integration.py:**
```python
import unittest
import json
import subprocess
import time
import os
import platform

class TestIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Start the service before tests"""
        # Start service in background
        if platform.system() == 'Windows':
            cls.service_process = subprocess.Popen(
                ['python', '-m', 'tpm_wrapper_service.service'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            cls.service_process = subprocess.Popen(
                ['python', '-m', 'tpm_wrapper_service.service'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        # Wait for service to start
        time.sleep(2)
    
    @classmethod
    def tearDownClass(cls):
        """Stop the service after tests"""
        cls.service_process.terminate()
        cls.service_process.wait()
    
    def test_service_starts(self):
        """Test that service starts successfully"""
        self.assertIsNotNone(self.service_process)
        self.assertEqual(self.service_process.poll(), None)  # Still running
    
    def test_get_ek_integration(self):
        """Test getEK command with real TPM"""
        # Use the test client code from above
        response = self.send_command('{"command": "getEK"}\n')
        
        self.assertEqual(response['status'], 'ok')
        self.assertIn('ek_public', response)
    
    def send_command(self, command):
        """Helper to send commands (implementation depends on platform)"""
        # Implementation from test_client.py above
        pass

if __name__ == '__main__':
    unittest.main()
```

---

### 4. Mock Testing (Without TPM Hardware)

For testing without a TPM chip:

**tests/test_with_mocks.py:**
```python
import unittest
from unittest.mock import Mock, MagicMock, patch
from tpm_wrapper_service import tpm_manager, ipc_server

class TestWithMocks(unittest.TestCase):
    
    @patch('tpm_wrapper_service.tpm_manager.ESYS')
    def test_get_ek_without_tpm(self, mock_esys):
        """Test getEK without real TPM"""
        # Create mock TPM context
        mock_ctx = MagicMock()
        
        # Mock ReadPublic to simulate existing EK
        mock_public = MagicMock()
        mock_public.type = 0x0001  # RSA
        mock_public.nameAlg = 0x000B  # SHA256
        mock_public.unique.rsa.size = 256
        mock_public.unique.rsa.buffer = bytes(256)
        mock_public.parameters.rsaDetail.exponent = 0
        
        mock_ctx.ReadPublic.return_value = (mock_public, None, None)
        
        # Test
        ek_handle, ek_public, ek_cert = tpm_manager.load_or_create_ek(mock_ctx)
        
        self.assertIsNotNone(ek_handle)
        self.assertIsNotNone(ek_public)

if __name__ == '__main__':
    unittest.main()
```

---

## Testing Checklist

### Basic Functionality
- [ ] Service starts successfully
- [ ] Service connects to TPM
- [ ] IPC server starts (pipe/socket created)
- [ ] Service handles shutdown gracefully

### Command Testing
- [ ] `getEK` returns valid EK public key
- [ ] `getEK` returns EK certificate (if available)
- [ ] `getAttestationData` returns EK and AIK
- [ ] `getAttestationData` returns valid AIK name
- [ ] `activateCredential` decrypts secrets (with real credentials)

### Error Handling
- [ ] Invalid JSON returns error
- [ ] Unknown command returns error
- [ ] Missing required fields returns error
- [ ] TPM errors are handled gracefully
- [ ] Client disconnection is handled

### Cross-Platform
- [ ] Works on Windows (x86_64)
- [ ] Works on Windows (ARM64) - if available
- [ ] Works on Linux (x86_64)
- [ ] Works on Linux (ARM64) - if available

### Security
- [ ] IPC channel is accessible (or properly restricted)
- [ ] TPM operations require proper permissions
- [ ] No sensitive data leaked in logs
- [ ] Proper error messages (no information disclosure)

---

## Testing Without TPM Hardware

### Option 1: TPM Simulator (Linux)

**Install TPM Simulator:**
```bash
# Install IBM TPM Simulator or Microsoft TPM Simulator
# Then point pytss to simulator instead of real TPM
```

### Option 2: Mock Everything

Use mocks for all TPM operations (see mock testing above).

### Option 3: Test Protocol Only

Test the IPC communication and JSON parsing without TPM operations.

---

## Continuous Integration (CI) Testing

**GitHub Actions example (.github/workflows/test.yml):**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: [3.8, 3.9, '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run unit tests
      run: |
        pytest tests/ --cov=tpm_wrapper_service
    
    - name: Run integration tests (if TPM available)
      run: |
        pytest tests/test_integration.py
      continue-on-error: true  # May not have TPM in CI
```

---

## Debugging Tips

### Enable Debug Logging
```python
# In service.py, change logging level
logging.basicConfig(level=logging.DEBUG)
```

### Check TPM Access
**Windows:**
```powershell
# Check TPM status
Get-Tpm

# Check if TPM is accessible
tpm.msc
```

**Linux:**
```bash
# Check TPM device
ls -l /dev/tpm*

# Check TPM info
tpm2_getcap properties-variable
```

### Common Issues

1. **Permission Denied**
   - Windows: Run as Administrator
   - Linux: Add user to `tss` group or use `sudo`

2. **TPM Not Found**
   - Check if TPM 2.0 is available
   - Check device permissions

3. **IPC Connection Failed**
   - Check if service is running
   - Check pipe/socket path
   - Check permissions on socket file (Linux)

---

## Performance Testing

**test_performance.py:**
```python
import time
import statistics

def benchmark_command(command, iterations=100):
    """Benchmark a command"""
    times = []
    
    for _ in range(iterations):
        start = time.time()
        response = send_command(command)
        elapsed = time.time() - start
        times.append(elapsed)
    
    print(f"Command: {command}")
    print(f"Average: {statistics.mean(times):.3f}s")
    print(f"Median: {statistics.median(times):.3f}s")
    print(f"Min: {min(times):.3f}s")
    print(f"Max: {max(times):.3f}s")

# Test performance
benchmark_command('{"command": "getEK"}\n')
benchmark_command('{"command": "getAttestationData"}\n')
```

---

## Summary

1. **Manual Testing**: Start service, use test client
2. **Unit Testing**: Test individual components with mocks
3. **Integration Testing**: Test with real TPM
4. **Mock Testing**: Test without TPM hardware
5. **CI Testing**: Automated tests in CI/CD pipeline

Choose the testing method based on:
- **Available hardware**: Real TPM vs simulator vs mocks
- **Test scope**: Unit vs integration vs end-to-end
- **Environment**: Local vs CI/CD

