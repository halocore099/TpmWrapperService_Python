#!/usr/bin/env python3
"""
Comprehensive test script for TPM Wrapper Service
Tests all features on both Linux and Windows
"""

import json
import sys
import platform
import time
import base64
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Test results storage
test_results: List[Dict] = []


def log_test(test_name: str, status: str, message: str = "", details: Dict = None):
    """Log a test result"""
    result = {
        "test": test_name,
        "status": status,  # "PASS", "FAIL", "SKIP", "WARN"
        "message": message,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    # Print status
    status_symbol = {
        "PASS": "✅",
        "FAIL": "❌",
        "SKIP": "⏭️",
        "WARN": "⚠️"
    }.get(status, "❓")
    
    print(f"{status_symbol} {test_name}: {status}")
    if message:
        print(f"   {message}")
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")


def get_ipc_path() -> str:
    """Get the IPC path based on platform"""
    if platform.system() == 'Windows':
        return r'\\.\pipe\TpmWrapperPipe'
    else:
        return '/tmp/TpmWrapperPipe.sock'


def send_command_windows(command: str) -> Optional[str]:
    """Send command via Windows named pipe"""
    try:
        import win32pipe
        import win32file
        import pywintypes
        
        pipe_name = get_ipc_path()
        
        # Try to connect
        try:
            pipe_handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
        except pywintypes.error as e:
            if e.winerror == 2:  # File not found
                return None
            raise
        
        # Send command
        win32file.WriteFile(pipe_handle, command.encode('utf-8'))
        
        # Read response
        result, data = win32file.ReadFile(pipe_handle, 4096)
        response = data.decode('utf-8')
        
        win32file.CloseHandle(pipe_handle)
        return response.strip()
        
    except ImportError:
        return None
    except Exception as e:
        raise Exception(f"Windows pipe error: {e}")


def send_command_linux(command: str) -> Optional[str]:
    """Send command via Linux Unix socket"""
    try:
        import socket
        
        socket_path = get_ipc_path()
        
        # Connect to Unix socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        sock.connect(socket_path)
        
        # Send command
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
        
        sock.close()
        return response_data.decode('utf-8').strip()
        
    except FileNotFoundError:
        return None
    except ConnectionRefusedError:
        return None
    except Exception as e:
        raise Exception(f"Linux socket error: {e}")


def send_command(command: str) -> Tuple[Optional[str], Optional[str]]:
    """Send command and return (response, error)"""
    try:
        if platform.system() == 'Windows':
            response = send_command_windows(command)
        else:
            response = send_command_linux(command)
        
        if response is None:
            return None, "Service not running or IPC path not accessible"
        
        return response, None
        
    except Exception as e:
        return None, str(e)


def test_service_running():
    """Test if service is running and accessible"""
    test_name = "Service Accessibility"
    
    try:
        # Try to connect (any command will do)
        test_cmd = json.dumps({"command": "getEK"}) + "\n"
        response, error = send_command(test_cmd)
        
        if error:
            log_test(test_name, "FAIL", f"Service not accessible: {error}")
            return False
        
        if response:
            log_test(test_name, "PASS", "Service is running and accessible")
            return True
        else:
            log_test(test_name, "FAIL", "No response from service")
            return False
            
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {e}")
        return False


def test_get_ek():
    """Test getEK command"""
    test_name = "getEK Command"
    
    try:
        command = json.dumps({"command": "getEK"}) + "\n"
        response_str, error = send_command(command)
        
        if error:
            log_test(test_name, "FAIL", f"Error: {error}")
            return False
        
        if not response_str:
            log_test(test_name, "FAIL", "No response received")
            return False
        
        try:
            response = json.loads(response_str)
        except json.JSONDecodeError as e:
            log_test(test_name, "FAIL", f"Invalid JSON response: {e}")
            return False
        
        # Check response structure
        if response.get('status') != 'ok':
            log_test(test_name, "FAIL", 
                    f"Status is not 'ok': {response.get('status')}",
                    {"response": response})
            return False
        
        # Check required fields
        if 'ek_public' not in response:
            log_test(test_name, "FAIL", "Missing 'ek_public' field", {"response": response})
            return False
        
        # Validate ek_public is base64
        try:
            ek_public_b64 = response['ek_public']
            base64.b64decode(ek_public_b64)
            ek_public_len = len(ek_public_b64)
        except Exception as e:
            log_test(test_name, "FAIL", f"Invalid base64 ek_public: {e}")
            return False
        
        # Check ek_cert (optional)
        ek_cert_present = response.get('ek_cert') is not None
        ek_cert_valid = False
        if ek_cert_present:
            try:
                base64.b64decode(response['ek_cert'])
                ek_cert_valid = True
            except:
                pass
        
        details = {
            "ek_public_length": ek_public_len,
            "ek_cert_present": ek_cert_present,
            "ek_cert_valid": ek_cert_valid if ek_cert_present else None
        }
        
        log_test(test_name, "PASS", "getEK command successful", details)
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {e}")
        return False


def test_get_attestation_data():
    """Test getAttestationData command"""
    test_name = "getAttestationData Command"
    
    try:
        command = json.dumps({"command": "getAttestationData"}) + "\n"
        response_str, error = send_command(command)
        
        if error:
            log_test(test_name, "FAIL", f"Error: {error}")
            return False
        
        if not response_str:
            log_test(test_name, "FAIL", "No response received")
            return False
        
        try:
            response = json.loads(response_str)
        except json.JSONDecodeError as e:
            log_test(test_name, "FAIL", f"Invalid JSON response: {e}")
            return False
        
        # Check response structure
        if response.get('status') != 'ok':
            log_test(test_name, "FAIL", 
                    f"Status is not 'ok': {response.get('status')}",
                    {"response": response})
            return False
        
        # Check required fields
        required_fields = ['ek_pub', 'aik_name']
        missing_fields = [f for f in required_fields if f not in response]
        
        if missing_fields:
            log_test(test_name, "FAIL", 
                    f"Missing required fields: {missing_fields}",
                    {"response": response})
            return False
        
        # Validate fields
        try:
            ek_pub_b64 = response['ek_pub']
            base64.b64decode(ek_pub_b64)
            ek_pub_len = len(ek_pub_b64)
        except Exception as e:
            log_test(test_name, "FAIL", f"Invalid base64 ek_pub: {e}")
            return False
        
        try:
            aik_name_b64 = response['aik_name']
            base64.b64decode(aik_name_b64)
            aik_name_len = len(aik_name_b64)
        except Exception as e:
            log_test(test_name, "FAIL", f"Invalid base64 aik_name: {e}")
            return False
        
        # Check ek_cert (optional)
        ek_cert_present = response.get('ek_cert') is not None
        
        details = {
            "ek_pub_length": ek_pub_len,
            "aik_name_length": aik_name_len,
            "ek_cert_present": ek_cert_present
        }
        
        log_test(test_name, "PASS", "getAttestationData command successful", details)
        return True
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {e}")
        return False


def test_activate_credential():
    """Test activateCredential command (may fail without real credentials)"""
    test_name = "activateCredential Command"
    
    try:
        # First get attestation data to understand the flow
        attestation_cmd = json.dumps({"command": "getAttestationData"}) + "\n"
        attestation_response, _ = send_command(attestation_cmd)
        
        if not attestation_response:
            log_test(test_name, "SKIP", 
                    "Cannot test - getAttestationData failed")
            return None
        
        # Try with invalid/mock data (will likely fail, but tests the command)
        command = json.dumps({
            "command": "activateCredential",
            "credential_blob": base64.b64encode(b"mock_blob").decode('ascii'),
            "encrypted_secret": base64.b64encode(b"mock_secret").decode('ascii'),
            "hmac": base64.b64encode(b"mock_hmac").decode('ascii'),
            "enc": base64.b64encode(b"mock_enc").decode('ascii')
        }) + "\n"
        
        response_str, error = send_command(command)
        
        if error:
            log_test(test_name, "WARN", 
                    f"Command failed (expected with mock data): {error}")
            return None
        
        if not response_str:
            log_test(test_name, "WARN", "No response received")
            return None
        
        try:
            response = json.loads(response_str)
        except json.JSONDecodeError as e:
            log_test(test_name, "FAIL", f"Invalid JSON response: {e}")
            return False
        
        # Check if it's an error (expected with mock data)
        if response.get('status') == 'error':
            log_test(test_name, "WARN", 
                    f"Command returned error (expected with mock data): {response.get('message')}",
                    {"note": "This is expected - real credentials are needed for full test"})
            return None
        
        # If it succeeded (unlikely with mock data), validate response
        if response.get('status') == 'ok':
            if 'decrypted_secret' not in response:
                log_test(test_name, "FAIL", "Missing 'decrypted_secret' field")
                return False
            
            try:
                base64.b64decode(response['decrypted_secret'])
                log_test(test_name, "PASS", 
                        "activateCredential command successful (unexpected with mock data!)",
                        {"note": "This is unusual - verify credentials are real"})
                return True
            except Exception as e:
                log_test(test_name, "FAIL", f"Invalid base64 decrypted_secret: {e}")
                return False
        
        log_test(test_name, "WARN", "Unexpected response format")
        return None
        
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {e}")
        return False


def test_invalid_command():
    """Test error handling with invalid command"""
    test_name = "Invalid Command Handling"
    
    try:
        command = json.dumps({"command": "invalidCommand123"}) + "\n"
        response_str, error = send_command(command)
        
        if error:
            log_test(test_name, "FAIL", f"Error sending command: {error}")
            return False
        
        if not response_str:
            log_test(test_name, "FAIL", "No response received")
            return False
        
        try:
            response = json.loads(response_str)
        except json.JSONDecodeError as e:
            log_test(test_name, "FAIL", f"Invalid JSON response: {e}")
            return False
        
        # Should return error status
        if response.get('status') == 'error':
            log_test(test_name, "PASS", 
                    "Service correctly returned error for invalid command",
                    {"error_message": response.get('message', 'N/A')})
            return True
        else:
            log_test(test_name, "FAIL", 
                    f"Service should return error but got: {response.get('status')}")
            return False
            
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {e}")
        return False


def test_malformed_json():
    """Test error handling with malformed JSON"""
    test_name = "Malformed JSON Handling"
    
    try:
        command = "this is not json\n"
        response_str, error = send_command(command)
        
        if error:
            log_test(test_name, "FAIL", f"Error sending command: {error}")
            return False
        
        if not response_str:
            log_test(test_name, "FAIL", "No response received")
            return False
        
        try:
            response = json.loads(response_str)
        except json.JSONDecodeError:
            log_test(test_name, "FAIL", "Service returned invalid JSON")
            return False
        
        # Should return error status
        if response.get('status') == 'error':
            log_test(test_name, "PASS", 
                    "Service correctly handled malformed JSON",
                    {"error_message": response.get('message', 'N/A')})
            return True
        else:
            log_test(test_name, "WARN", 
                    f"Service returned: {response.get('status')} (expected error)")
            return None
            
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {e}")
        return False


def test_missing_fields():
    """Test error handling with missing required fields"""
    test_name = "Missing Fields Handling"
    
    try:
        # Test activateCredential with missing fields
        command = json.dumps({"command": "activateCredential"}) + "\n"
        response_str, error = send_command(command)
        
        if error:
            log_test(test_name, "FAIL", f"Error sending command: {error}")
            return False
        
        if not response_str:
            log_test(test_name, "FAIL", "No response received")
            return False
        
        try:
            response = json.loads(response_str)
        except json.JSONDecodeError as e:
            log_test(test_name, "FAIL", f"Invalid JSON response: {e}")
            return False
        
        # Should return error status
        if response.get('status') == 'error':
            log_test(test_name, "PASS", 
                    "Service correctly returned error for missing fields",
                    {"error_message": response.get('message', 'N/A')})
            return True
        else:
            log_test(test_name, "FAIL", 
                    f"Service should return error but got: {response.get('status')}")
            return False
            
    except Exception as e:
        log_test(test_name, "FAIL", f"Exception: {e}")
        return False


def generate_report():
    """Generate a comprehensive test report"""
    print("\n" + "="*70)
    print("TEST REPORT")
    print("="*70)
    
    # Summary
    total = len(test_results)
    passed = len([r for r in test_results if r['status'] == 'PASS'])
    failed = len([r for r in test_results if r['status'] == 'FAIL'])
    skipped = len([r for r in test_results if r['status'] == 'SKIP'])
    warned = len([r for r in test_results if r['status'] == 'WARN'])
    
    print(f"\nPlatform: {platform.system()} ({platform.machine()})")
    print(f"Python: {sys.version.split()[0]}")
    print(f"\nSummary:")
    print(f"  Total Tests: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⚠️  Warnings: {warned}")
    print(f"  ⏭️  Skipped: {skipped}")
    
    # Detailed results
    print(f"\n{'='*70}")
    print("DETAILED RESULTS")
    print("="*70)
    
    for result in test_results:
        status_symbol = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⏭️",
            "WARN": "⚠️"
        }.get(result['status'], "❓")
        
        print(f"\n{status_symbol} {result['test']}")
        print(f"   Status: {result['status']}")
        if result['message']:
            print(f"   Message: {result['message']}")
        if result['details']:
            print(f"   Details:")
            for key, value in result['details'].items():
                print(f"     - {key}: {value}")
        print(f"   Time: {result['timestamp']}")
    
    # Recommendations
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print("="*70)
    
    if failed > 0:
        print("\n⚠️  Some tests failed. Check the details above.")
        failed_tests = [r['test'] for r in test_results if r['status'] == 'FAIL']
        print(f"   Failed tests: {', '.join(failed_tests)}")
    
    if skipped > 0:
        print("\n⏭️  Some tests were skipped (may require additional setup).")
    
    if warned > 0:
        print("\n⚠️  Some tests produced warnings (may be expected behavior).")
    
    if passed == total and failed == 0:
        print("\n✅ All tests passed!")
    
    # Platform-specific notes
    print(f"\n{'='*70}")
    print("PLATFORM NOTES")
    print("="*70)
    
    if platform.system() == 'Windows':
        print("\nWindows-specific:")
        print("  - Using Windows Named Pipes for IPC")
        print("  - TPM access via TBS (TPM Base Services)")
        print("  - Requires pywin32 for named pipe access")
    else:
        print("\nLinux-specific:")
        print("  - Using Unix Domain Sockets for IPC")
        print("  - TPM access via /dev/tpm0 or /dev/tpmrm0")
        print("  - May require user to be in 'tss' group")
        print("  - Check TPM device permissions if tests fail")
    
    # Save report to file
    report_file = f"test_report_{platform.system().lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "platform": platform.system(),
            "architecture": platform.machine(),
            "python_version": sys.version,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "warned": warned
            },
            "results": test_results
        }, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_file}")


def main():
    """Run all tests"""
    print("="*70)
    print("TPM WRAPPER SERVICE - COMPREHENSIVE TEST SUITE")
    print("="*70)
    print(f"\nPlatform: {platform.system()} ({platform.machine()})")
    print(f"IPC Path: {get_ipc_path()}")
    print(f"\nStarting tests...\n")
    
    # Check prerequisites
    if platform.system() == 'Windows':
        try:
            import win32pipe
            import win32file
        except ImportError:
            print("❌ ERROR: pywin32 not installed. Install with: pip install pywin32")
            sys.exit(1)
    
    # Run tests
    print("\n" + "-"*70)
    print("RUNNING TESTS")
    print("-"*70 + "\n")
    
    # Test 1: Service accessibility
    if not test_service_running():
        print("\n⚠️  Service is not running or not accessible.")
        print("   Please start the service first:")
        print("   python -m tpm_wrapper_service.service")
        print("\n   Continuing with remaining tests anyway...\n")
    
    # Test 2: getEK
    test_get_ek()
    time.sleep(0.5)  # Small delay between tests
    
    # Test 3: getAttestationData
    test_get_attestation_data()
    time.sleep(0.5)
    
    # Test 4: activateCredential (may fail without real credentials)
    test_activate_credential()
    time.sleep(0.5)
    
    # Test 5: Error handling - invalid command
    test_invalid_command()
    time.sleep(0.5)
    
    # Test 6: Error handling - malformed JSON
    test_malformed_json()
    time.sleep(0.5)
    
    # Test 7: Error handling - missing fields
    test_missing_fields()
    
    # Generate report
    generate_report()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

