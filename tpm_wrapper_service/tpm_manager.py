"""
TPM Manager - Core TPM operations
"""
import logging
from typing import Tuple, Optional
from cryptography import x509
from cryptography.hazmat.backends import default_backend

try:
    from TSS import TSS
    from TSS import ESYS
    from TSS import TPM2
except ImportError:
    # Fallback for different pytss import paths
    try:
        import tpm2_pytss as TSS
        ESYS = TSS.ESYS
        TPM2 = TSS.TPM2
    except ImportError:
        raise ImportError("pytss or tpm2-pytss is required. Install with: pip install pytss")

logger = logging.getLogger(__name__)

# TPM NV Index for RSA EK Cert
EK_CERT_NV_INDEX = 0x01C00002

# EK template policy (from TCG EK Credential Profile)
EK_POLICY = bytes([
    0x83, 0x71, 0x97, 0x67, 0x44, 0x84, 0xB3, 0xF8,
    0x1A, 0x90, 0xCC, 0x8D, 0x46, 0xA5, 0xD7, 0x24,
    0xFD, 0x52, 0xD7, 0x6E, 0x06, 0x52, 0x0B, 0x64,
    0xF2, 0xA1, 0xDA, 0x1B, 0x33, 0x14, 0x69, 0xAA
])


def load_or_create_ek(ctx: ESYS.ESYS_CONTEXT) -> Tuple[ESYS.ESYS_TR, dict, Optional[x509.Certificate]]:
    """
    Load existing EK or create a new one.
    
    Returns:
        Tuple of (ek_handle, ek_public_dict, ek_cert)
    """
    try:
        # Try to read existing EK from endorsement hierarchy
        ek_handle = ESYS.ESYS_TR.ENDORSEMENT
        ek_public, _, _ = ctx.ReadPublic(ek_handle)
        logger.info("Loaded existing EK")
        
        ek_public_dict = {
            'type': ek_public.type,
            'nameAlg': ek_public.nameAlg,
            'objectAttributes': ek_public.objectAttributes,
            'authPolicy': ek_public.authPolicy.buffer if ek_public.authPolicy else None,
            'parameters': {
                'symmetric': {
                    'algorithm': ek_public.parameters.rsaDetail.symmetric.algorithm,
                    'keyBits': ek_public.parameters.rsaDetail.symmetric.keyBits.aes,
                    'mode': ek_public.parameters.rsaDetail.symmetric.mode.aes
                },
                'scheme': {
                    'scheme': ek_public.parameters.rsaDetail.scheme.scheme,
                },
                'keyBits': ek_public.parameters.rsaDetail.keyBits,
                'exponent': ek_public.parameters.rsaDetail.exponent
            },
            'unique': {
                'size': ek_public.unique.rsa.size,
                'buffer': bytes(ek_public.unique.rsa.buffer[:ek_public.unique.rsa.size])
            }
        }
        
    except Exception as e:
        logger.info(f"Creating EK... (error: {e})")
        
        # Create EK template
        ek_template = TPM2.TPMT_PUBLIC(
            type=TPM2.TPM2_ALG_RSA,
            nameAlg=TPM2.TPM2_ALG_SHA256,
            objectAttributes=(
                TPM2.TPMA_OBJECT.FIXEDTPM |
                TPM2.TPMA_OBJECT.FIXEDPARENT |
                TPM2.TPMA_OBJECT.RESTRICTED |
                TPM2.TPMA_OBJECT.DECRYPT |
                TPM2.TPMA_OBJECT.ADMINWITHPOLICY |
                TPM2.TPMA_OBJECT.SENSITIVEDATAORIGIN
            ),
            authPolicy=TPM2.TPM2B_DIGEST(buffer=EK_POLICY),
            parameters=TPM2.TPMS_RSA_PARMS(
                symmetric=TPM2.TPMT_SYM_DEF_OBJECT(
                    algorithm=TPM2.TPM2_ALG_AES,
                    keyBits=TPM2.TPMU_SYM_KEY_BITS(aes=128),
                    mode=TPM2.TPMU_SYM_MODE(aes=TPM2.TPM2_ALG_CFB)
                ),
                scheme=TPM2.TPMT_RSA_SCHEME(scheme=TPM2.TPM2_ALG_NULL),
                keyBits=2048,
                exponent=0
            ),
            unique=TPM2.TPMU_PUBLIC_ID(rsa=TPM2.TPM2B_PUBLIC_KEY_RSA(buffer=bytes(256)))
        )
        
        # Create primary key in endorsement hierarchy
        ek_handle, ek_public, _, _, _ = ctx.CreatePrimary(
            ESYS.ESYS_TR.ENDORSEMENT,
            ESYS.ESYS_TR.NONE,
            ESYS.ESYS_TR.NONE,
            ESYS.ESYS_TR.NONE,
            None,
            ek_template,
            None,
            None
        )
        
        logger.info("Created EK")
        
        ek_public_dict = {
            'type': ek_public.type,
            'nameAlg': ek_public.nameAlg,
            'objectAttributes': ek_public.objectAttributes,
            'authPolicy': ek_public.authPolicy.buffer if ek_public.authPolicy else None,
            'parameters': {
                'symmetric': {
                    'algorithm': ek_public.parameters.rsaDetail.symmetric.algorithm,
                    'keyBits': ek_public.parameters.rsaDetail.symmetric.keyBits.aes,
                    'mode': ek_public.parameters.rsaDetail.symmetric.mode.aes
                },
                'scheme': {
                    'scheme': ek_public.parameters.rsaDetail.scheme.scheme,
                },
                'keyBits': ek_public.parameters.rsaDetail.keyBits,
                'exponent': ek_public.parameters.rsaDetail.exponent
            },
            'unique': {
                'size': ek_public.unique.rsa.size,
                'buffer': bytes(ek_public.unique.rsa.buffer[:ek_public.unique.rsa.size])
            }
        }
    
    # Try to read EK certificate from NV storage
    ek_cert = None
    try:
        ek_cert_bytes = read_ek_cert_from_nv(ctx, EK_CERT_NV_INDEX)
        if ek_cert_bytes:
            ek_cert = x509.load_der_x509_certificate(ek_cert_bytes, default_backend())
            
            # Validate certificate matches EK public key
            # (simplified - full validation would compare modulus)
            logger.info("Loaded EK certificate from NV storage")
    except Exception as e:
        logger.warning(f"Failed to read/compare EK Certificate: {e}")
    
    return ek_handle, ek_public_dict, ek_cert


def read_ek_cert_from_nv(ctx: ESYS.ESYS_CONTEXT, nv_index: int) -> Optional[bytes]:
    """Read EK certificate from NV storage."""
    try:
        nv_handle = ESYS.ESYS_TR.NV(nv_index)
        nv_public, _ = ctx.NV_ReadPublic(nv_handle)
        cert_size = nv_public.dataSize
        
        cert_data = bytearray()
        offset = 0
        max_read_size = 1024
        
        while offset < cert_size:
            bytes_to_read = min(max_read_size, cert_size - offset)
            chunk = ctx.NV_Read(
                nv_handle,
                nv_handle,
                bytes_to_read,
                offset
            )
            cert_data.extend(chunk)
            offset += bytes_to_read
        
        # Unwrap if needed (TPM2B format)
        if len(cert_data) > 2:
            wrapped_length = (cert_data[0] << 8) | cert_data[1]
            if wrapped_length + 2 == len(cert_data):
                return bytes(cert_data[2:])
        
        return bytes(cert_data)
    except Exception as e:
        logger.warning(f"Failed to read NV index {nv_index:X}: {e}")
        return None


def normalize_modulus(modulus: bytes) -> bytes:
    """Remove leading zeros from modulus."""
    offset = 0
    while offset < len(modulus) and modulus[offset] == 0:
        offset += 1
    return modulus[offset:]


def create_or_load_aik_transient(ctx: ESYS.ESYS_CONTEXT) -> Tuple[ESYS.ESYS_TR, dict]:
    """
    Create a transient AIK (Attestation Identity Key).
    
    Returns:
        Tuple of (aik_handle, aik_public_dict)
    """
    # Define AIK template (ECC P-256)
    aik_template = TPM2.TPMT_PUBLIC(
        type=TPM2.TPM2_ALG_ECC,
        nameAlg=TPM2.TPM2_ALG_SHA256,
        objectAttributes=(
            TPM2.TPMA_OBJECT.FIXEDTPM |
            TPM2.TPMA_OBJECT.FIXEDPARENT |
            TPM2.TPMA_OBJECT.SENSITIVEDATAORIGIN |
            TPM2.TPMA_OBJECT.USERWITHAUTH |
            TPM2.TPMA_OBJECT.SIGN |
            TPM2.TPMA_OBJECT.RESTRICTED
        ),
        authPolicy=TPM2.TPM2B_DIGEST(),
        parameters=TPM2.TPMS_ECC_PARMS(
            symmetric=TPM2.TPMT_SYM_DEF_OBJECT(
                algorithm=TPM2.TPM2_ALG_NULL
            ),
            scheme=TPM2.TPMT_ECC_SCHEME(
                scheme=TPM2.TPM2_ALG_ECDSA,
                details=TPM2.TPMU_ASYM_SCHEME(ecdsa=TPM2.TPMT_SIG_SCHEME(
                    scheme=TPM2.TPM2_ALG_ECDSA,
                    details=TPM2.TPMU_SIG_SCHEME(ecdsa=TPM2.TPMS_SCHEME_ECDSA(
                        hashAlg=TPM2.TPM2_ALG_SHA256
                    ))
                ))
            ),
            curveID=TPM2.TPM2_ECC_NIST_P256,
            kdf=TPM2.TPMT_KDF_SCHEME(scheme=TPM2.TPM2_ALG_NULL)
        ),
        unique=TPM2.TPMU_PUBLIC_ID(ecc=TPM2.TPMS_ECC_POINT(
            x=TPM2.TPM2B_ECC_PARAMETER(buffer=bytes(32)),
            y=TPM2.TPM2B_ECC_PARAMETER(buffer=bytes(32))
        ))
    )
    
    # Create AIK as transient object
    aik_handle, aik_public, _, _, _ = ctx.CreatePrimary(
        ESYS.ESYS_TR.ENDORSEMENT,
        ESYS.ESYS_TR.NONE,
        ESYS.ESYS_TR.NONE,
        ESYS.ESYS_TR.NONE,
        None,
        aik_template,
        None,
        None
    )
    
    # Get AIK name
    aik_name = ctx.GetName(aik_handle)
    
    aik_public_dict = {
        'type': aik_public.type,
        'nameAlg': aik_public.nameAlg,
        'name': aik_name
    }
    
    return aik_handle, aik_public_dict


def activate_credential(
    ctx: ESYS.ESYS_CONTEXT,
    aik_handle: ESYS.ESYS_TR,
    ek_handle: ESYS.ESYS_TR,
    credential_blob: bytes,
    encrypted_secret: bytes
) -> bytes:
    """
    Activate credential using EK and AIK.
    
    Args:
        ctx: TPM context
        aik_handle: AIK handle
        ek_handle: EK handle
        credential_blob: Credential blob (IdObject)
        encrypted_secret: Encrypted secret
    
    Returns:
        Decrypted secret
    """
    # Start policy session
    policy_session = ctx.StartAuthSession(
        ESYS.ESYS_TR.NONE,
        ESYS.ESYS_TR.NONE,
        None,
        ESYS.ESYS_TR.NONE,
        ESYS.ESYS_TR.NONE,
        None,
        TPM2.TPM2_SE.POLICY,
        TPM2.TPMT_SYM_DEF(algorithm=TPM2.TPM2_ALG_NULL),
        TPM2.TPM2_ALG_SHA256
    )
    
    try:
        # PolicySecret for endorsement hierarchy
        ctx.PolicySecret(
            ESYS.ESYS_TR.ENDORSEMENT,
            policy_session,
            ESYS.ESYS_TR.NONE,
            ESYS.ESYS_TR.NONE,
            ESYS.ESYS_TR.NONE,
            None,
            None,
            None,
            0
        )
        
        # Parse credential blob (IdObject format: HMAC + ENC)
        # For simplicity, assuming credential_blob is already parsed
        # In practice, you'd parse the TPM2B_ID_OBJECT structure
        
        # Activate credential
        decrypted_secret = ctx.ActivateCredential(
            aik_handle,
            ek_handle,
            policy_session,
            ESYS.ESYS_TR.NONE,
            ESYS.ESYS_TR.NONE,
            credential_blob,
            encrypted_secret
        )
        
        return decrypted_secret
    finally:
        ctx.FlushContext(policy_session)

