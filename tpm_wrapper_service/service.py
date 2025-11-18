"""
Main service entry point - Cross-platform TPM wrapper service
"""
import asyncio
import logging
import signal
import sys
from typing import Optional

from . import platform_utils
from . import ipc_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tpm_wrapper_service.log')
    ]
)

logger = logging.getLogger(__name__)


def get_tpm_context():
    """Get TPM context based on platform."""
    try:
        from TSS import ESYS
        # Try TSS library first
        ctx = ESYS.ESYS_CONTEXT()
        ctx.connect()
        return ctx
    except ImportError:
        try:
            # Fallback to tpm2-pytss
            import tpm2_pytss as TSS
            ctx = TSS.ESYS.ESYS_CONTEXT()
            ctx.connect()
            return ctx
        except ImportError:
            raise ImportError(
                "No TPM library found. Install pytss or tpm2-pytss:\n"
                "  pip install pytss\n"
                "  or\n"
                "  pip install tpm2-pytss"
            )


class TpmWrapperService:
    """Main TPM wrapper service."""
    
    def __init__(self):
        self.tpm_ctx: Optional[object] = None
        self.ipc_server: Optional[ipc_server.IPCServer] = None
        self.running = False
        
    async def start(self):
        """Start the service."""
        try:
            logger.info("Starting TPM Wrapper Service...")
            logger.info(f"Platform: {sys.platform}, Architecture: {platform_utils.get_architecture()}")
            
            # Connect to TPM
            self.tpm_ctx = get_tpm_context()
            logger.info("Connected to TPM")
            
            # Start IPC server
            self.ipc_server = ipc_server.IPCServer(self.tpm_ctx)
            self.running = True
            
            # Start listening
            await self.ipc_server.start_listening()
            
        except Exception as e:
            logger.error(f"Failed to start service: {e}", exc_info=True)
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the service."""
        logger.info("Stopping TPM Wrapper Service...")
        self.running = False
        
        if self.tpm_ctx:
            try:
                self.tpm_ctx.close()
            except Exception as e:
                logger.warning(f"Error closing TPM context: {e}")
        
        logger.info("Service stopped.")


async def main():
    """Main entry point."""
    service = TpmWrapperService()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Service error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await service.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

