"""
EK (Endorsement Key) export utilities
Converts TPM RSA public keys to X.509 SubjectPublicKeyInfo format
"""
import struct
import sys
from typing import Tuple


def export_rsa_ek_to_base64_x509(modulus: bytes, exponent: int) -> str:
    """
    Export RSA EK to base64-encoded X.509 SubjectPublicKeyInfo format.
    
    Args:
        modulus: RSA modulus bytes
        exponent: RSA exponent (defaults to 65537 if 0)
    
    Returns:
        Base64-encoded X.509 SubjectPublicKeyInfo
    """
    import base64
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    
    # Default exponent is 65537
    if exponent == 0:
        exponent = 65537
    
    # Create RSA public key from modulus and exponent
    public_numbers = rsa.RSAPublicNumbers(
        e=exponent,
        n=int.from_bytes(modulus, byteorder='big', signed=False)
    )
    public_key = public_numbers.public_key()
    
    # Export as X.509 SubjectPublicKeyInfo
    x509_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return base64.b64encode(x509_bytes).decode('ascii')

