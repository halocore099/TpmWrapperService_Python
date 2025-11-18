#!/usr/bin/env python3
"""
TPM Registration Client
Connects to TPM Wrapper Service and registers with remote server
"""

import json
import sys
import platform
import uuid
import base64
import requests
from typing import Optional, Dict

# Configuration
TPM_SERVICE_IPC_PATH = None  # Will be set based on platform
SERVER_URL = None  # Set this to your server IP/URL


def get_ipc_path() -> str:
    """Get the IPC path based on platform"""
    if platform.system() == 'Windows':
        return r'\\.\pipe\TpmWrapperPipe'
    else:
        return '/tmp/TpmWrapperPipe.sock'


def send_command_to_tpm_service(command: dict) -> Optional[Dict]:
    """Send command to TPM Wrapper Service and return response"""
    command_str = json.dumps(command) + "\n"
    
    try:
        if platform.system() == 'Windows':
            import win32pipe
            import win32file
            import pywintypes
            
            pipe_name = get_ipc_path()
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
                    print(f"❌ Error: TPM service not running or pipe not found")
                    return None
                raise
            
            win32file.WriteFile(pipe_handle, command_str.encode('utf-8'))
            result, data = win32file.ReadFile(pipe_handle, 4096)
            response_str = data.decode('utf-8')
            win32file.CloseHandle(pipe_handle)
            
        else:
            import socket
            
            socket_path = get_ipc_path()
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(socket_path)
            
            sock.sendall(command_str.encode('utf-8'))
            response_data = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b'\n' in response_data:
                    break
            
            sock.close()
            response_str = response_data.decode('utf-8').strip()
        
        # Parse response
        response = json.loads(response_str)
        return response
        
    except FileNotFoundError:
        print(f"❌ Error: TPM service not running or socket not found")
        return None
    except ConnectionRefusedError:
        print(f"❌ Error: Could not connect to TPM service")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON response from TPM service: {e}")
        return None
    except Exception as e:
        print(f"❌ Error communicating with TPM service: {e}")
        return None


def get_attestation_data() -> Optional[Dict]:
    """Get attestation data from TPM service"""
    print("📡 Getting attestation data from TPM service...")
    
    command = {"command": "getAttestationData"}
    response = send_command_to_tpm_service(command)
    
    if not response:
        return None
    
    if response.get('status') != 'ok':
        print(f"❌ Error from TPM service: {response.get('message', 'Unknown error')}")
        return None
    
    print("✅ Got attestation data from TPM")
    return response


def register_with_server(attestation_data: Dict, server_url: str, user_uuid: str = None) -> Optional[Dict]:
    """Register with the remote server"""
    print(f"\n🌐 Registering with server: {server_url}")
    
    # Generate UUID if not provided
    if not user_uuid:
        user_uuid = str(uuid.uuid4())
        print(f"📝 Generated UUID: {user_uuid}")
    
    # Prepare registration request
    register_data = {
        "uuid": user_uuid,
        "ek_pub": attestation_data.get('ek_pub'),
        "aik_name": attestation_data.get('aik_name'),
        "ek_cert": attestation_data.get('ek_cert')  # May be None
    }
    
    try:
        response = requests.post(
            f"{server_url}/register",
            json=register_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        print("✅ Registration successful")
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error registering with server: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Server response: {error_detail}")
            except:
                print(f"   Server response: {e.response.text}")
        return None


def activate_credential(credential_blob: str, encrypted_secret: str, hmac: str, enc: str) -> Optional[str]:
    """Activate credential using TPM service"""
    print("\n🔐 Activating credential with TPM...")
    
    command = {
        "command": "activateCredential",
        "credential_blob": credential_blob,
        "encrypted_secret": encrypted_secret,
        "hmac": hmac,
        "enc": enc
    }
    
    response = send_command_to_tpm_service(command)
    
    if not response:
        return None
    
    if response.get('status') != 'ok':
        print(f"❌ Error activating credential: {response.get('message', 'Unknown error')}")
        return None
    
    decrypted_secret = response.get('decrypted_secret')
    if not decrypted_secret:
        print("❌ Error: No decrypted_secret in response")
        return None
    
    print("✅ Credential activated successfully")
    return decrypted_secret


def complete_challenge(server_url: str, challenge_id: str, decrypted_secret: str) -> bool:
    """Complete the challenge with the server"""
    print(f"\n✅ Completing challenge with server...")
    
    complete_data = {
        "challenge_id": challenge_id,
        "decrypted_secret": decrypted_secret
    }
    
    try:
        response = requests.post(
            f"{server_url}/completeChallenge",
            json=complete_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        print("✅ Challenge completed successfully!")
        print(f"   Server response: {result}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error completing challenge: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Server response: {error_detail}")
            except:
                print(f"   Server response: {e.response.text}")
        return False


def main():
    """Main registration flow"""
    print("="*70)
    print("TPM Registration Client")
    print("="*70)
    
    # Get server URL
    if len(sys.argv) > 1:
        server_url = sys.argv[1].rstrip('/')  # Remove trailing slash
    else:
        server_url = input("Enter server URL (e.g., http://192.168.1.100:8000): ").strip().rstrip('/')
    
    if not server_url:
        print("❌ Error: Server URL is required")
        sys.exit(1)
    
    print(f"\n🎯 Target server: {server_url}")
    
    # Step 1: Get attestation data from TPM service
    attestation_data = get_attestation_data()
    if not attestation_data:
        print("\n❌ Failed to get attestation data. Make sure TPM service is running.")
        sys.exit(1)
    
    # Step 2: Register with server
    register_response = register_with_server(attestation_data, server_url)
    if not register_response:
        print("\n❌ Registration failed")
        sys.exit(1)
    
    # Extract challenge data from server response
    # The server should return something like:
    # {
    #   "challenge_id": "...",
    #   "credential_blob": "...",
    #   "encrypted_secret": "...",
    #   "hmac": "...",
    #   "enc": "..."
    # }
    
    challenge_id = register_response.get('challenge_id')
    if not challenge_id:
        print("❌ Error: Server did not return challenge_id")
        print(f"   Server response: {register_response}")
        sys.exit(1)
    
    print(f"📋 Received challenge_id: {challenge_id}")
    
    # Check if server sent credential data directly, or if we need to request it
    credential_blob = register_response.get('credential_blob')
    encrypted_secret = register_response.get('encrypted_secret')
    hmac = register_response.get('hmac')
    enc = register_response.get('enc')
    
    if not all([credential_blob, encrypted_secret, hmac, enc]):
        print("⚠️  Server response doesn't include credential data")
        print("   You may need to request the challenge separately")
        print(f"   Server response: {register_response}")
        # You might need to make another API call here to get the challenge
        sys.exit(1)
    
    # Step 3: Activate credential
    decrypted_secret = activate_credential(credential_blob, encrypted_secret, hmac, enc)
    if not decrypted_secret:
        print("\n❌ Failed to activate credential")
        sys.exit(1)
    
    # Step 4: Complete challenge
    success = complete_challenge(server_url, challenge_id, decrypted_secret)
    
    if success:
        print("\n" + "="*70)
        print("✅ REGISTRATION COMPLETE!")
        print("="*70)
        sys.exit(0)
    else:
        print("\n" + "="*70)
        print("❌ REGISTRATION FAILED")
        print("="*70)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

