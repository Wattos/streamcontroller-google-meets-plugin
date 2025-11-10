"""
Authentication Module

Handles cryptographic operations and pairing management for StreamController.
"""

from .crypto_manager import CryptoManager
from .pairing_manager import PairingManager, PairingRequest

__all__ = ["CryptoManager", "PairingManager", "PairingRequest"]
