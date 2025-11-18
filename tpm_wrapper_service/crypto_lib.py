"""
Cryptographic utilities
"""
import secrets


def random_bytes(length: int) -> bytes:
    """Generate cryptographically secure random bytes."""
    return secrets.token_bytes(length)

