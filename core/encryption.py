"""File encryption utilities using cryptography library."""

import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from core.logging import get_logger

logger = get_logger(__name__)


class FileEncryption:
    """File-level encryption using Fernet (symmetric encryption)."""

    def __init__(self, encryption_key: str | None = None):
        """Initialize encryption with key from environment or provided key."""
        if encryption_key is None:
            encryption_key = os.getenv("ENCRYPTION_KEY")

        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable must be set or provided"
            )

        try:
            self.cipher = Fernet(encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}") from e

    def encrypt_file(self, source_path: Path, dest_path: Path) -> None:
        """Encrypt a file and save to destination."""
        try:
            with open(source_path, "rb") as f:
                file_data = f.read()

            encrypted_data = self.cipher.encrypt(file_data)

            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_path, "wb") as f:
                f.write(encrypted_data)

            logger.info("File encrypted", source=str(source_path), dest=str(dest_path))
        except Exception as e:
            logger.error("Encryption failed", error=str(e), path=str(source_path))
            raise

    def decrypt_file(self, source_path: Path, dest_path: Path) -> None:
        """Decrypt a file and save to destination."""
        try:
            with open(source_path, "rb") as f:
                encrypted_data = f.read()

            try:
                decrypted_data = self.cipher.decrypt(encrypted_data)
            except InvalidToken:
                logger.error("Decryption failed: invalid token", path=str(source_path))
                raise ValueError("Invalid encryption token") from None

            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            with open(dest_path, "wb") as f:
                f.write(decrypted_data)

            logger.info("File decrypted", source=str(source_path), dest=str(dest_path))
        except Exception as e:
            logger.error("Decryption failed", error=str(e), path=str(source_path))
            raise

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()

