"""
Cross-platform IPC server (Named Pipes on Windows, Unix Domain Sockets on Linux)
"""
import asyncio
import json
import logging
import os
import sys
from typing import Optional

from . import platform_utils
from . import tpm_manager
from . import ek_exporter
from . import crypto_lib

logger = logging.getLogger(__name__)

try:
    from TSS import ESYS
except ImportError:
    try:
        import tpm2_pytss as TSS
        ESYS = TSS.ESYS
    except ImportError:
        raise ImportError("pytss or tpm2-pytss is required")


class IPCServer:
    """Cross-platform IPC server for TPM operations."""
    
    def __init__(self, tpm_ctx: ESYS.ESYS_CONTEXT):
        self.tpm_ctx = tpm_ctx
        self.pipe_name = platform_utils.get_pipe_name()
        self.server = None
        
    async def start_listening(self):
        """Start listening for client connections."""
        logger.info(f"IPC Server started on {self.pipe_name}")
        
        if platform_utils.is_windows():
            await self._start_windows_named_pipe()
        else:
            await self._start_unix_socket()
    
    async def _start_windows_named_pipe(self):
        """Start Windows named pipe server."""
        import win32pipe
        import win32file
        import pywintypes
        
        while True:
            try:
                # Create named pipe
                pipe_handle = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    1,  # Max instances
                    4096,  # Out buffer size
                    4096,  # In buffer size
                    0,  # Default timeout
                    None  # Security attributes (all users for now)
                )
                
                logger.info("Waiting for client connection...")
                # Use overlapped I/O for async
                overlapped = pywintypes.OVERLAPPED()
                win32pipe.ConnectNamedPipe(pipe_handle, overlapped)
                # Wait for connection in executor to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    None, win32file.GetOverlappedResult, pipe_handle, overlapped, True
                )
                logger.info("Client connected.")
                
                try:
                    await self._handle_client_windows(pipe_handle)
                except Exception as e:
                    logger.error(f"Error handling client: {e}")
                finally:
                    win32file.CloseHandle(pipe_handle)
                    
            except pywintypes.error as e:
                if e.winerror != 535:  # Ignore "pipe is being closed" errors
                    logger.error(f"Named pipe error: {e}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(1)
    
    async def _handle_client_windows(self, pipe_handle):
        """Handle Windows named pipe client."""
        import win32file
        import pywintypes
        
        buffer = bytearray()
        
        while True:
            try:
                # Use overlapped I/O for async read
                overlapped = pywintypes.OVERLAPPED()
                result, data = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: win32file.ReadFile(pipe_handle, 4096, overlapped)
                )
                
                if not data:
                    logger.info("Client disconnected.")
                    break
                
                buffer.extend(data)
                message = buffer.decode('utf-8', errors='ignore')
                
                if '\n' in message:
                    newline_idx = message.index('\n')
                    request = message[:newline_idx].strip('\r')
                    logger.info(f"Received: {request}")
                    
                    response = self._handle_request(request) + '\n'
                    response_bytes = response.encode('utf-8')
                    
                    # Write response
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: win32file.WriteFile(pipe_handle, response_bytes)
                    )
                    logger.info(f"Response sent: {response.strip()}")
                    
                    # Remove processed message
                    buffer = bytearray(message[newline_idx + 1:].encode('utf-8'))
                    
                    break
            except Exception as e:
                logger.error(f"Error reading from pipe: {e}")
                break
    
    async def _start_unix_socket(self):
        """Start Unix domain socket server."""
        # Remove socket file if it exists
        if os.path.exists(self.pipe_name):
            os.unlink(self.pipe_name)
        
        self.server = await asyncio.start_unix_server(
            self._handle_client_unix,
            self.pipe_name
        )
        
        # Set socket permissions (read/write for all users - adjust for security)
        os.chmod(self.pipe_name, 0o666)
        
        logger.info(f"Unix socket server listening on {self.pipe_name}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def _handle_client_unix(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle Unix socket client."""
        try:
            logger.info("Client connected.")
            
            buffer = bytearray()
            
            while True:
                data = await reader.read(4096)
                if not data:
                    logger.info("Client disconnected.")
                    break
                
                buffer.extend(data)
                message = buffer.decode('utf-8', errors='ignore')
                
                if '\n' in message:
                    newline_idx = message.index('\n')
                    request = message[:newline_idx].strip('\r')
                    logger.info(f"Received: {request}")
                    
                    response = self._handle_request(request) + '\n'
                    response_bytes = response.encode('utf-8')
                    
                    writer.write(response_bytes)
                    await writer.drain()
                    logger.info(f"Response sent: {response.strip()}")
                    
                    # Remove processed message
                    buffer = bytearray(message[newline_idx + 1:].encode('utf-8'))
                    
                    break
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    def _handle_request(self, json_str: str) -> str:
        """Handle incoming JSON request."""
        try:
            command = json.loads(json_str)
            cmd = command.get('command')
            
            if cmd == 'getEK':
                return self._handle_get_ek()
            elif cmd == 'getAttestationData':
                return self._handle_get_attestation_data()
            elif cmd == 'activateCredential':
                return self._handle_activate_credential(command)
            else:
                return json.dumps({'status': 'error', 'message': 'Unknown command'})
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return json.dumps({'status': 'error', 'message': str(e)})
    
    def _handle_get_ek(self) -> str:
        """Handle getEK command."""
        try:
            ek_handle, ek_public_dict, ek_cert = tpm_manager.load_or_create_ek(self.tpm_ctx)
            
            # Export EK public key
            modulus = ek_public_dict['unique']['buffer']
            exponent = ek_public_dict['parameters'].get('exponent', 0)
            ek_public_b64 = ek_exporter.export_rsa_ek_to_base64_x509(modulus, exponent)
            
            # Flush EK handle
            try:
                self.tpm_ctx.FlushContext(ek_handle)
            except Exception as e:
                logger.warning(f"Error flushing EK handle: {e}")
            
            result = {
                'status': 'ok',
                'ek_public': ek_public_b64,
                'ek_cert': None
            }
            
            if ek_cert:
                from cryptography.hazmat.primitives import serialization
                cert_bytes = ek_cert.public_bytes(serialization.Encoding.DER)
                import base64
                result['ek_cert'] = base64.b64encode(cert_bytes).decode('ascii')
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error in getEK: {e}", exc_info=True)
            return json.dumps({'status': 'error', 'message': str(e)})
    
    def _handle_get_attestation_data(self) -> str:
        """Handle getAttestationData command."""
        try:
            ek_handle, ek_public_dict, ek_cert = tpm_manager.load_or_create_ek(self.tpm_ctx)
            
            # Export EK public key
            modulus = ek_public_dict['unique']['buffer']
            exponent = ek_public_dict['parameters'].get('exponent', 0)
            ek_public_b64 = ek_exporter.export_rsa_ek_to_base64_x509(modulus, exponent)
            
            # Flush EK handle
            try:
                self.tpm_ctx.FlushContext(ek_handle)
            except Exception as e:
                logger.warning(f"Error flushing EK handle: {e}")
            
            # Create AIK
            aik_handle, aik_public_dict = tpm_manager.create_or_load_aik_transient(self.tpm_ctx)
            
            if aik_handle is None:
                return json.dumps({'status': 'error', 'message': 'Failed to create AIK handle'})
            
            # Get AIK name (convert to base64)
            aik_name = aik_public_dict.get('name', b'')
            if isinstance(aik_name, bytes):
                import base64
                aik_name_b64 = base64.b64encode(aik_name).decode('ascii')
            else:
                aik_name_b64 = str(aik_name)
            
            # Flush AIK handle
            try:
                self.tpm_ctx.FlushContext(aik_handle)
            except Exception as e:
                logger.warning(f"Error flushing AIK handle: {e}")
            
            result = {
                'status': 'ok',
                'ek_pub': ek_public_b64,
                'ek_cert': None,
                'aik_name': aik_name_b64
            }
            
            if ek_cert:
                from cryptography.hazmat.primitives import serialization
                cert_bytes = ek_cert.public_bytes(serialization.Encoding.DER)
                import base64
                result['ek_cert'] = base64.b64encode(cert_bytes).decode('ascii')
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error in getAttestationData: {e}", exc_info=True)
            return json.dumps({'status': 'error', 'message': str(e)})
    
    def _handle_activate_credential(self, command: dict) -> str:
        """Handle activateCredential command."""
        try:
            if not all(k in command for k in ['credential_blob', 'encrypted_secret', 'hmac', 'enc']):
                return json.dumps({'status': 'error', 'message': 'Missing required fields'})
            
            import base64
            
            encrypted_secret = base64.b64decode(command['encrypted_secret'])
            hmac = base64.b64decode(command['hmac'])
            enc = base64.b64decode(command['enc'])
            
            # Reconstruct credential blob (IdObject format)
            # In practice, you'd properly construct TPM2B_ID_OBJECT
            credential_blob = hmac + enc  # Simplified
            
            # Load EK and AIK
            ek_handle, _, _ = tpm_manager.load_or_create_ek(self.tpm_ctx)
            aik_handle, _ = tpm_manager.create_or_load_aik_transient(self.tpm_ctx)
            
            # Activate credential
            decrypted_secret = tpm_manager.activate_credential(
                self.tpm_ctx,
                aik_handle,
                ek_handle,
                credential_blob,
                encrypted_secret
            )
            
            # Flush handles
            try:
                self.tpm_ctx.FlushContext(ek_handle)
                self.tpm_ctx.FlushContext(aik_handle)
            except Exception as e:
                logger.warning(f"Error flushing handles: {e}")
            
            return json.dumps({
                'status': 'ok',
                'decrypted_secret': base64.b64encode(decrypted_secret).decode('ascii')
            })
        except Exception as e:
            logger.error(f"Error in activateCredential: {e}", exc_info=True)
            return json.dumps({'status': 'error', 'message': f'ActivateCredential failed: {str(e)}'})

