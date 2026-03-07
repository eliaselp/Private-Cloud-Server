# app/crypto_utils.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64
import logging

logger = logging.getLogger(__name__)

class FileEncryptor:
    def __init__(self, key=None):
        """Inicializa el cifrador con una clave Fernet."""
        from flask import current_app
        
        if key is None:
            key = current_app.config['ENCRYPTION_KEY']
        
        if isinstance(key, str):
            key = key.encode()
        
        # Verificar que la clave es válida para Fernet
        try:
            self.cipher = Fernet(key)
        except Exception as e:
            logger.error(f"Invalid encryption key: {e}")
            raise ValueError("La clave de cifrado no es válida. Debe ser una clave Fernet de 32 bytes en base64.")
    
    def encrypt_file(self, source_path, dest_path, chunk_size=64*1024):
        """
        Cifra un archivo en chunks para manejar archivos grandes.
        Formato: [tamaño_chunk(4 bytes)][datos_cifrados]...
        """
        try:
            with open(source_path, 'rb') as source_file:
                with open(dest_path, 'wb') as dest_file:
                    while True:
                        chunk = source_file.read(chunk_size)
                        if not chunk:
                            break
                        
                        encrypted_chunk = self.cipher.encrypt(chunk)
                        
                        # Escribir tamaño del chunk cifrado (4 bytes) y luego el chunk
                        dest_file.write(len(encrypted_chunk).to_bytes(4, 'big'))
                        dest_file.write(encrypted_chunk)
            
            logger.info(f"File encrypted successfully: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error encrypting file {source_path}: {e}")
            # Si hay error, eliminar archivo destino si existe
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise
    
    def decrypt_file(self, source_path, dest_path):
        """
        Descifra un archivo cifrado con encrypt_file.
        """
        try:
            with open(source_path, 'rb') as source_file:
                with open(dest_path, 'wb') as dest_file:
                    while True:
                        # Leer tamaño del chunk cifrado (4 bytes)
                        size_data = source_file.read(4)
                        if not size_data:
                            break
                        
                        chunk_size = int.from_bytes(size_data, 'big')
                        
                        # Leer chunk cifrado
                        encrypted_chunk = source_file.read(chunk_size)
                        if not encrypted_chunk:
                            break
                        
                        # Descifrar
                        decrypted_chunk = self.cipher.decrypt(encrypted_chunk)
                        dest_file.write(decrypted_chunk)
            
            logger.info(f"File decrypted successfully: {source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error decrypting file {source_path}: {e}")
            # Si hay error, eliminar archivo destino si existe
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise
    
    def encrypt_memory_file(self, data):
        """Cifra datos en memoria."""
        return self.cipher.encrypt(data)
    
    def decrypt_memory_file(self, encrypted_data):
        """Descifra datos en memoria."""
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_file_object(self, file_object, dest_path, chunk_size=64*1024):
        """
        Cifra directamente desde un objeto file-like (útil para uploads).
        """
        try:
            with open(dest_path, 'wb') as dest_file:
                while True:
                    chunk = file_object.read(chunk_size)
                    if not chunk:
                        break
                    
                    encrypted_chunk = self.cipher.encrypt(chunk)
                    dest_file.write(len(encrypted_chunk).to_bytes(4, 'big'))
                    dest_file.write(encrypted_chunk)
            
            return True
        except Exception as e:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise

def generate_encryption_key():
    """Genera una clave Fernet válida."""
    return Fernet.generate_key().decode()

def verify_encryption_key(key):
    """Verifica si una clave es válida para Fernet."""
    try:
        if isinstance(key, str):
            key = key.encode()
        Fernet(key)
        return True
    except:
        return False