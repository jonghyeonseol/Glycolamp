"""
ALCOA++ Checksum Manager

Implements the ENDURING principle through cryptographic file integrity verification.
All data files are hashed with SHA-256 to ensure data has not been altered.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional


class ChecksumManager:
    """
    Manages SHA-256 checksums for data integrity (ENDURING principle)

    Ensures that data files have not been tampered with or corrupted
    during storage and transmission.
    """

    def __init__(self, checksum_file: str = "Results/audit_trail/file_checksums.json"):
        """
        Initialize checksum manager

        Parameters
        ----------
        checksum_file : str
            Path to JSON file storing all checksums
        """
        self.checksum_file = Path(checksum_file)
        self.checksum_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing checksums if available
        self.checksums: Dict[str, str] = {}
        if self.checksum_file.exists():
            with open(self.checksum_file, 'r', encoding='utf-8') as f:
                self.checksums = json.load(f)

    def calculate_checksum(self, file_path: str) -> str:
        """
        Calculate SHA-256 checksum for a file

        Parameters
        ----------
        file_path : str
            Path to file

        Returns
        -------
        str
            Hexadecimal SHA-256 hash
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def register_file(self, file_path: str) -> str:
        """
        Register a file and calculate its checksum

        Parameters
        ----------
        file_path : str
            Path to file to register

        Returns
        -------
        str
            SHA-256 checksum
        """
        file_path = str(Path(file_path).resolve())  # Absolute path
        checksum = self.calculate_checksum(file_path)

        self.checksums[file_path] = checksum
        self._save_checksums()

        return checksum

    def verify_file(self, file_path: str) -> bool:
        """
        Verify file integrity against stored checksum

        Parameters
        ----------
        file_path : str
            Path to file to verify

        Returns
        -------
        bool
            True if file matches stored checksum, False otherwise

        Raises
        ------
        ValueError
            If file has no stored checksum
        """
        file_path = str(Path(file_path).resolve())

        if file_path not in self.checksums:
            raise ValueError(f"No checksum found for {file_path}. Register file first.")

        current_checksum = self.calculate_checksum(file_path)
        stored_checksum = self.checksums[file_path]

        return current_checksum == stored_checksum

    def _save_checksums(self):
        """Save checksums to JSON file"""
        with open(self.checksum_file, 'w', encoding='utf-8') as f:
            json.dump(self.checksums, f, indent=2)

    def get_checksum(self, file_path: str) -> Optional[str]:
        """
        Retrieve stored checksum for a file

        Parameters
        ----------
        file_path : str
            Path to file

        Returns
        -------
        str or None
            Stored checksum, or None if not found
        """
        file_path = str(Path(file_path).resolve())
        return self.checksums.get(file_path)

    def get_all_checksums(self) -> Dict[str, str]:
        """Get all registered checksums"""
        return self.checksums.copy()
