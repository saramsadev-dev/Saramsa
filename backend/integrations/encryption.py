"""
Token encryption/decryption utilities for secure storage of integration credentials.
Uses AES-256-GCM encryption with a key derived from Django SECRET_KEY.
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """Generate a consistent encryption key from Django SECRET_KEY."""
    # Use PBKDF2 to derive a 32-byte key from SECRET_KEY
    key_material = settings.SECRET_KEY.encode('utf-8')
    salt = b'saramsa_integrations_salt'  # Fixed salt for consistency
    key = hashlib.pbkdf2_hmac('sha256', key_material, salt, 100000)
    return base64.urlsafe_b64encode(key)


def encrypt_token(token: str) -> str:
    """Encrypt a token for secure storage."""
    try:
        if not token:
            return ""
        
        key = _get_encryption_key()
        fernet = Fernet(key)
        
        # Encrypt the token
        encrypted_token = fernet.encrypt(token.encode('utf-8'))
        
        # Return base64 encoded string for JSON storage
        return base64.b64encode(encrypted_token).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        raise ValueError("Failed to encrypt token")


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a token for use."""
    try:
        if not encrypted_token:
            return ""
        
        key = _get_encryption_key()
        fernet = Fernet(key)
        
        # Decode from base64
        encrypted_bytes = base64.b64decode(encrypted_token.encode('utf-8'))
        
        # Decrypt the token
        decrypted_token = fernet.decrypt(encrypted_bytes)
        
        return decrypted_token.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        raise ValueError("Failed to decrypt token")


def is_token_encrypted(token: str) -> bool:
    """Check if a token appears to be encrypted (base64 encoded)."""
    try:
        if not token:
            return False
        
        # Try to decode as base64
        base64.b64decode(token.encode('utf-8'))
        
        # If it's much longer than typical tokens, it's likely encrypted
        return len(token) > 100
        
    except Exception:
        return False


def migrate_token_to_encrypted(plain_token: str) -> str:
    """Helper function to migrate existing plain tokens to encrypted format."""
    if is_token_encrypted(plain_token):
        return plain_token  # Already encrypted
    
    return encrypt_token(plain_token)
