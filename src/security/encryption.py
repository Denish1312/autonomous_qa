"""
Service for handling data encryption and key management.
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.fernet import Fernet
import os
import base64
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from .models import EncryptionAlgorithm, EncryptedData

class KeyManager:
    """Manages encryption keys and key rotation"""
    
    def __init__(self, key_store_path: str = "./data/keys"):
        self.key_store_path = key_store_path
        os.makedirs(key_store_path, exist_ok=True)
        self.active_key_id = None
        self.keys: Dict[str, bytes] = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load encryption keys from storage"""
        key_files = os.listdir(self.key_store_path)
        for key_file in key_files:
            if key_file.endswith('.key'):
                key_id = key_file[:-4]
                with open(os.path.join(self.key_store_path, key_file), 'rb') as f:
                    self.keys[key_id] = f.read()
                if not self.active_key_id:
                    self.active_key_id = key_id
    
    def generate_key(self) -> str:
        """Generate a new encryption key"""
        key_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        key = os.urandom(32)  # 256-bit key
        
        # Save key to storage
        key_path = os.path.join(self.key_store_path, f"{key_id}.key")
        with open(key_path, 'wb') as f:
            f.write(key)
        
        self.keys[key_id] = key
        self.active_key_id = key_id
        return key_id
    
    def get_active_key(self) -> Tuple[str, bytes]:
        """Get the currently active encryption key"""
        if not self.active_key_id:
            self.active_key_id = self.generate_key()
        return self.active_key_id, self.keys[self.active_key_id]
    
    def get_key(self, key_id: str) -> Optional[bytes]:
        """Get a specific encryption key by ID"""
        return self.keys.get(key_id)

class EncryptionService:
    """Handles data encryption and decryption"""
    
    def __init__(self):
        self.key_manager = KeyManager()
    
    def _get_cipher(self, algorithm: EncryptionAlgorithm, key: bytes):
        """Get the appropriate cipher based on algorithm"""
        if algorithm == EncryptionAlgorithm.AES_256_GCM:
            return AESGCM(key)
        elif algorithm == EncryptionAlgorithm.CHACHA20_POLY1305:
            return ChaCha20Poly1305(key)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    def encrypt(
        self,
        data: Dict[str, Any],
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    ) -> EncryptedData:
        """
        Encrypt data using the specified algorithm.
        Returns EncryptedData model with all necessary information for decryption.
        """
        key_id, key = self.key_manager.get_active_key()
        cipher = self._get_cipher(algorithm, key)
        
        # Convert data to bytes
        data_bytes = json.dumps(data).encode()
        
        # Generate nonce
        nonce = os.urandom(12)  # 96 bits as recommended for GCM
        
        # Encrypt data
        ciphertext = cipher.encrypt(nonce, data_bytes, None)
        
        return EncryptedData(
            algorithm=algorithm,
            ciphertext=ciphertext[:-16],  # Separate ciphertext from tag
            tag=ciphertext[-16:],  # Last 16 bytes are the authentication tag
            nonce=nonce,
            key_id=key_id
        )
    
    def decrypt(self, encrypted_data: EncryptedData) -> Dict[str, Any]:
        """
        Decrypt data using the stored encryption parameters.
        Returns the original data dictionary.
        """
        key = self.key_manager.get_key(encrypted_data.key_id)
        if not key:
            raise ValueError(f"Key not found: {encrypted_data.key_id}")
        
        cipher = self._get_cipher(encrypted_data.algorithm, key)
        
        # Combine ciphertext and tag
        ciphertext_with_tag = encrypted_data.ciphertext + encrypted_data.tag
        
        # Decrypt data
        try:
            decrypted_bytes = cipher.decrypt(
                encrypted_data.nonce,
                ciphertext_with_tag,
                None
            )
            return json.loads(decrypted_bytes.decode())
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def rotate_keys(self):
        """
        Rotate encryption keys and re-encrypt all data with the new key.
        This should be called periodically as part of security maintenance.
        """
        # Generate new key
        new_key_id = self.key_manager.generate_key()
        
        # TODO: Implement data re-encryption with new key
        # This would involve:
        # 1. Finding all encrypted data
        # 2. Decrypting with old key
        # 3. Encrypting with new key
        # 4. Updating storage
        # 5. Removing old key if no longer needed
        
        return new_key_id

class PasswordHasher:
    """Handles secure password hashing"""
    
    def __init__(self, iterations: int = 100000):
        self.iterations = iterations
    
    def hash_password(self, password: str) -> Tuple[str, str]:
        """
        Hash a password using PBKDF2 with a random salt.
        Returns (hash, salt) both base64 encoded.
        """
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
        )
        hash_bytes = kdf.derive(password.encode())
        return (
            base64.b64encode(hash_bytes).decode(),
            base64.b64encode(salt).decode()
        )
    
    def verify_password(
        self,
        password: str,
        hash_b64: str,
        salt_b64: str
    ) -> bool:
        """Verify a password against its hash and salt"""
        hash_bytes = base64.b64decode(hash_b64)
        salt = base64.b64decode(salt_b64)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
        )
        
        try:
            kdf.verify(password.encode(), hash_bytes)
            return True
        except:
            return False
