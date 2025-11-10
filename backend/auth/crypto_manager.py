"""
Crypto Manager

Handles all cryptographic operations for authentication:
- JWS (JSON Web Signature) verification with ES256
- Public key validation
"""

import json
from typing import Optional, Dict
from loguru import logger as log
import jwt


class CryptoManager:
    """Handles cryptographic operations"""

    @staticmethod
    def verify_jws(token: str, public_key_jwk: Dict) -> Optional[Dict]:
        """
        Verify JWS token with ES256 algorithm

        Args:
            token: JWT token string
            public_key_jwk: Public key in JWK format

        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            # Convert JWK dict to JSON string for PyJWT
            public_key_json = json.dumps(public_key_jwk)

            # Load public key from JWK
            public_key = jwt.algorithms.ECAlgorithm.from_jwk(public_key_json)

            # Verify and decode JWT
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["ES256"]
            )

            log.debug(f"JWT verified successfully for instance: {payload.get('instance_id', 'unknown')}")
            return payload

        except jwt.ExpiredSignatureError:
            log.error("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            log.error(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            log.error(f"Error verifying JWT: {e}")
            return None

    @staticmethod
    def validate_public_key(public_key_jwk: Dict) -> bool:
        """
        Validate that public key JWK is correctly formatted

        Args:
            public_key_jwk: Public key in JWK format

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields for EC key
            if public_key_jwk.get('kty') != 'EC':
                log.error(f"Invalid key type: {public_key_jwk.get('kty')}")
                return False

            if public_key_jwk.get('crv') != 'P-256':
                log.error(f"Invalid curve: {public_key_jwk.get('crv')}")
                return False

            # Check for x and y coordinates
            if not public_key_jwk.get('x') or not public_key_jwk.get('y'):
                log.error("Missing x or y coordinates in public key")
                return False

            # Try to load it
            public_key_json = json.dumps(public_key_jwk)
            jwt.algorithms.ECAlgorithm.from_jwk(public_key_json)

            return True

        except Exception as e:
            log.error(f"Error validating public key: {e}")
            return False
