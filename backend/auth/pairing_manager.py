"""
Pairing Manager

Handles pairing requests and instance authorization:
- Stores pending pairing requests
- Manages authorized instances with public keys
- Persists authorization data
"""

import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from loguru import logger as log


@dataclass
class PairingRequest:
    """Represents a pairing request from a browser extension instance"""
    extension_id: str
    instance_id: str
    public_key: Dict  # JWK format
    metadata: Dict  # Browser info, extension name, etc.
    timestamp: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'PairingRequest':
        """Create from dictionary"""
        return cls(**data)


class PairingManager:
    """Manages pairing requests and authorized instances"""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize pairing manager

        Args:
            storage_path: Path to storage file (default: ./pairing_data.json)
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent / "pairing_data.json"

        self.storage_path = storage_path
        self.pending_requests: Dict[Tuple[str, str], PairingRequest] = {}
        self.authorized_instances: Dict[Tuple[str, str], PairingRequest] = {}

        # Load existing data
        self._load()

    def request_pairing(self, extension_id: str, instance_id: str,
                       public_key: Dict, metadata: Dict) -> PairingRequest:
        """
        Create a new pairing request

        Args:
            extension_id: Extension ID
            instance_id: Instance ID (UUID)
            public_key: Public key in JWK format
            metadata: Browser and extension metadata

        Returns:
            Created PairingRequest object
        """
        key = (extension_id, instance_id)

        # Check if already authorized
        if key in self.authorized_instances:
            log.info(f"Instance {instance_id} already authorized for {extension_id}")
            return self.authorized_instances[key]

        # Create new request
        request = PairingRequest(
            extension_id=extension_id,
            instance_id=instance_id,
            public_key=public_key,
            metadata=metadata,
            timestamp=time.time()
        )

        self.pending_requests[key] = request
        self._save()

        log.info(f"New pairing request from {extension_id} (instance: {instance_id})")
        log.debug(f"Metadata: {metadata}")

        return request

    def approve_instance(self, extension_id: str, instance_id: str) -> bool:
        """
        Approve a pending pairing request

        Args:
            extension_id: Extension ID
            instance_id: Instance ID

        Returns:
            True if approved, False if not found
        """
        key = (extension_id, instance_id)

        if key not in self.pending_requests:
            log.warning(f"No pending request found for {extension_id}/{instance_id}")
            return False

        # Move from pending to authorized
        request = self.pending_requests.pop(key)
        self.authorized_instances[key] = request
        self._save()

        log.info(f"Approved pairing for {extension_id} (instance: {instance_id})")

        return True

    def deny_instance(self, extension_id: str, instance_id: str) -> bool:
        """
        Deny a pending pairing request

        Args:
            extension_id: Extension ID
            instance_id: Instance ID

        Returns:
            True if denied, False if not found
        """
        key = (extension_id, instance_id)

        if key not in self.pending_requests:
            log.warning(f"No pending request found for {extension_id}/{instance_id}")
            return False

        # Remove from pending
        self.pending_requests.pop(key)
        self._save()

        log.info(f"Denied pairing for {extension_id} (instance: {instance_id})")

        return True

    def revoke_instance(self, extension_id: str, instance_id: str) -> bool:
        """
        Revoke authorization for an instance

        Args:
            extension_id: Extension ID
            instance_id: Instance ID

        Returns:
            True if revoked, False if not found
        """
        key = (extension_id, instance_id)

        if key not in self.authorized_instances:
            log.warning(f"No authorized instance found for {extension_id}/{instance_id}")
            return False

        # Remove from authorized
        self.authorized_instances.pop(key)
        self._save()

        log.info(f"Revoked authorization for {extension_id} (instance: {instance_id})")

        return True

    def is_authorized(self, extension_id: str, instance_id: str) -> bool:
        """
        Check if an instance is authorized

        Args:
            extension_id: Extension ID
            instance_id: Instance ID

        Returns:
            True if authorized, False otherwise
        """
        key = (extension_id, instance_id)
        return key in self.authorized_instances

    def get_public_key(self, extension_id: str, instance_id: str) -> Optional[Dict]:
        """
        Get public key for an authorized instance

        Args:
            extension_id: Extension ID
            instance_id: Instance ID

        Returns:
            Public key in JWK format, or None if not authorized
        """
        key = (extension_id, instance_id)

        if key not in self.authorized_instances:
            return None

        return self.authorized_instances[key].public_key

    def get_pending_requests(self) -> List[PairingRequest]:
        """
        Get all pending pairing requests

        Returns:
            List of PairingRequest objects
        """
        return list(self.pending_requests.values())

    def get_authorized_instances(self, extension_id: Optional[str] = None) -> List[PairingRequest]:
        """
        Get all authorized instances, optionally filtered by extension ID

        Args:
            extension_id: Optional extension ID to filter by

        Returns:
            List of PairingRequest objects
        """
        if extension_id is None:
            return list(self.authorized_instances.values())

        return [
            request for (ext_id, _), request in self.authorized_instances.items()
            if ext_id == extension_id
        ]

    def clear_old_pending_requests(self, max_age_seconds: int = 300) -> int:
        """
        Clear pending requests older than specified age

        Args:
            max_age_seconds: Maximum age in seconds (default: 5 minutes)

        Returns:
            Number of requests cleared
        """
        current_time = time.time()
        to_remove = []

        for key, request in self.pending_requests.items():
            age = current_time - request.timestamp
            if age > max_age_seconds:
                to_remove.append(key)

        for key in to_remove:
            self.pending_requests.pop(key)
            log.info(f"Cleared old pending request: {key}")

        if to_remove:
            self._save()

        return len(to_remove)

    def _save(self):
        """Save pairing data to disk"""
        try:
            data = {
                'pending': {
                    f"{ext_id}:{inst_id}": request.to_dict()
                    for (ext_id, inst_id), request in self.pending_requests.items()
                },
                'authorized': {
                    f"{ext_id}:{inst_id}": request.to_dict()
                    for (ext_id, inst_id), request in self.authorized_instances.items()
                }
            }

            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

            log.debug(f"Saved pairing data to {self.storage_path}")

        except Exception as e:
            log.error(f"Error saving pairing data: {e}")

    def _load(self):
        """Load pairing data from disk"""
        if not self.storage_path.exists():
            log.info("No existing pairing data found")
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)

            # Load pending requests
            for key_str, request_data in data.get('pending', {}).items():
                ext_id, inst_id = key_str.split(':', 1)
                key = (ext_id, inst_id)
                self.pending_requests[key] = PairingRequest.from_dict(request_data)

            # Load authorized instances
            for key_str, request_data in data.get('authorized', {}).items():
                ext_id, inst_id = key_str.split(':', 1)
                key = (ext_id, inst_id)
                self.authorized_instances[key] = PairingRequest.from_dict(request_data)

            log.info(f"Loaded {len(self.pending_requests)} pending and "
                    f"{len(self.authorized_instances)} authorized instances")

        except Exception as e:
            log.error(f"Error loading pairing data: {e}")
