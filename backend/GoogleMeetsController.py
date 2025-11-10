import asyncio
import json
import time
from typing import Dict, Optional, Callable, Any
from loguru import logger as log
import websockets
from websockets.server import WebSocketServerProtocol

from auth import CryptoManager, PairingManager, PairingRequest


class GoogleMeetsController:
    """
    Handles WebSocket server for Google Meet Chrome extension communication.

    Features:
    - WebSocket server on localhost
    - Pairing protocol with user approval (instance-based)
    - JWS (ES256) authentication with asymmetric keys
    - State synchronization (mic, camera, hand)
    - Command forwarding to extension
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.loop = None
        self.connected = False

        # Authentication managers
        self.crypto = CryptoManager()
        self.pairing = PairingManager()

        # Client management
        self.active_connection: Optional[WebSocketServerProtocol] = None
        self.extension_id: Optional[str] = None
        self.instance_id: Optional[str] = None

        # State tracking
        self.current_state = {
            "mic_enabled": False,
            "camera_enabled": False,
            "hand_raised": False,
            "in_meeting": False,
            "meeting_id": None,
            "meeting_name": None,
            "participant_count": 0,
        }

        # Callbacks for state updates
        self.state_update_callbacks: list[Callable] = []

        # Pending pairing approval requests (key: (extension_id, instance_id))
        self.pending_approval: Dict[tuple[str, str], asyncio.Future] = {}

    def add_state_update_callback(self, callback: Callable[[Dict], None]):
        """Register callback for state updates"""
        self.state_update_callbacks.append(callback)

    def remove_state_update_callback(self, callback: Callable[[Dict], None]):
        """Unregister callback for state updates"""
        if callback in self.state_update_callbacks:
            self.state_update_callbacks.remove(callback)

    def _notify_state_update(self):
        """Notify all callbacks of state update"""
        for callback in self.state_update_callbacks:
            try:
                callback(self.current_state.copy())
            except Exception as e:
                log.error(f"Error in state update callback: {e}")

    def revoke_instance(self, extension_id: str, instance_id: str):
        """Revoke approval for an instance"""
        self.pairing.revoke_instance(extension_id, instance_id)

        # Disconnect if currently connected
        if self.extension_id == extension_id and self.instance_id == instance_id and self.active_connection:
            asyncio.create_task(self.active_connection.close(1000, "Instance revoked"))

    def request_approval(self, pairing_request: PairingRequest) -> asyncio.Future:
        """
        Request user approval for pairing.
        Returns a Future that will be resolved when user approves/denies.
        """
        key = (pairing_request.extension_id, pairing_request.instance_id)

        # Check if already authorized
        if self.pairing.is_authorized(pairing_request.extension_id, pairing_request.instance_id):
            future = asyncio.Future()
            future.set_result(True)
            return future

        # Create pending approval future
        future = asyncio.Future()
        self.pending_approval[key] = future
        log.info(f"Approval requested for {pairing_request.extension_id} (instance: {pairing_request.instance_id})")
        return future

    def approve_instance(self, extension_id: str, instance_id: str):
        """Approve a pending instance"""
        self.pairing.approve_instance(extension_id, instance_id)

        key = (extension_id, instance_id)
        if key in self.pending_approval:
            future = self.pending_approval.pop(key)
            if not future.done():
                future.set_result(True)
        log.info(f"Instance approved: {extension_id}/{instance_id}")

    def deny_instance(self, extension_id: str, instance_id: str):
        """Deny a pending instance"""
        self.pairing.deny_instance(extension_id, instance_id)

        key = (extension_id, instance_id)
        if key in self.pending_approval:
            future = self.pending_approval.pop(key)
            if not future.done():
                future.set_result(False)
        log.info(f"Instance denied: {extension_id}/{instance_id}")

    def _verify_message(self, data: Dict) -> Optional[Dict]:
        """
        Verify JWS signature and extract payload

        Args:
            data: Message data with token field

        Returns:
            Decoded payload if valid, None otherwise
        """
        # Extract fields
        extension_id = data.get("extension_id")
        instance_id = data.get("instance_id")
        token = data.get("token")

        if not extension_id or not instance_id or not token:
            log.error("Missing required fields in message")
            return None

        # Check if instance is authorized
        if not self.pairing.is_authorized(extension_id, instance_id):
            log.error(f"Unauthorized instance: {extension_id}/{instance_id}")
            return None

        # Get public key
        public_key = self.pairing.get_public_key(extension_id, instance_id)
        if not public_key:
            log.error(f"No public key found for {extension_id}/{instance_id}")
            return None

        # Verify JWS signature
        payload = self.crypto.verify_jws(token, public_key)
        if not payload:
            log.error(f"JWS verification failed for {extension_id}/{instance_id}")
            return None

        # Verify instance_id matches
        if payload.get("instance_id") != instance_id:
            log.error("Instance ID mismatch in JWT payload")
            return None

        return payload

    async def _handle_handshake(self, websocket: WebSocketServerProtocol, data: Dict) -> bool:
        """
        Handle pairing/handshake protocol:
        1. Extension sends public key, instance_id, and metadata
        2. Server validates public key format
        3. Server creates pairing request
        4. Server requests user approval (if not already authorized)
        5. If approved, stores authorization and responds with success
        """
        # Extract fields
        extension_id = data.get("extension_id")
        instance_id = data.get("instance_id")
        public_key = data.get("public_key")
        metadata = data.get("metadata", {})

        # Validate required fields
        if not extension_id:
            await websocket.send(json.dumps({
                "type": "error",
                "error_code": "missing_field",
                "message": "Missing extension_id in handshake"
            }))
            return False

        if not instance_id:
            await websocket.send(json.dumps({
                "type": "error",
                "error_code": "missing_field",
                "message": "Missing instance_id in handshake"
            }))
            return False

        if not public_key:
            await websocket.send(json.dumps({
                "type": "error",
                "error_code": "missing_field",
                "message": "Missing public_key in handshake"
            }))
            return False

        # Validate public key format
        if not self.crypto.validate_public_key(public_key):
            await websocket.send(json.dumps({
                "type": "error",
                "error_code": "invalid_key",
                "message": "Invalid public key format"
            }))
            return False

        # Create/update pairing request
        pairing_request = self.pairing.request_pairing(
            extension_id=extension_id,
            instance_id=instance_id,
            public_key=public_key,
            metadata=metadata
        )

        # Check if already authorized
        if self.pairing.is_authorized(extension_id, instance_id):
            log.info(f"Instance already authorized: {extension_id}/{instance_id}")
            self.extension_id = extension_id
            self.instance_id = instance_id
            self.active_connection = websocket
            self.connected = True

            await websocket.send(json.dumps({
                "type": "handshake_success",
                "message": "Already authorized"
            }))
            return True

        # Request approval from user
        log.info(f"Requesting approval for new instance: {extension_id}/{instance_id}")
        approval_future = self.request_approval(pairing_request)

        # Send pending response
        await websocket.send(json.dumps({
            "type": "handshake_pending",
            "message": "Awaiting user approval"
        }))

        # Wait for approval (with timeout)
        try:
            approved = await asyncio.wait_for(approval_future, timeout=60.0)
            if not approved:
                await websocket.send(json.dumps({
                    "type": "handshake_denied",
                    "message": "User denied pairing"
                }))
                return False
        except asyncio.TimeoutError:
            await websocket.send(json.dumps({
                "type": "handshake_timeout",
                "message": "Approval request timed out"
            }))
            return False

        # Pairing approved
        self.extension_id = extension_id
        self.instance_id = instance_id
        self.active_connection = websocket
        self.connected = True

        await websocket.send(json.dumps({
            "type": "handshake_success",
            "message": "Pairing approved"
        }))

        log.info(f"Handshake successful with {extension_id} (instance: {instance_id})")
        return True

    async def _handle_state_update(self, data: Dict):
        """Handle state update from extension"""
        state_data = data.get("data", {})

        # Update internal state
        if "mic_enabled" in state_data:
            self.current_state["mic_enabled"] = state_data["mic_enabled"]
        if "camera_enabled" in state_data:
            self.current_state["camera_enabled"] = state_data["camera_enabled"]
        if "hand_raised" in state_data:
            self.current_state["hand_raised"] = state_data["hand_raised"]
        if "in_meeting" in state_data:
            self.current_state["in_meeting"] = state_data["in_meeting"]
        if "meeting_id" in state_data:
            self.current_state["meeting_id"] = state_data["meeting_id"]
        if "meeting_name" in state_data:
            self.current_state["meeting_name"] = state_data["meeting_name"]
        if "participant_count" in state_data:
            self.current_state["participant_count"] = state_data["participant_count"]

        # Notify callbacks
        self._notify_state_update()
        log.debug(f"State updated: {self.current_state}")

    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            # Handshake doesn't require authentication
            if msg_type == "handshake":
                await self._handle_handshake(websocket, data)
                return

            # All other messages require JWS authentication
            payload = self._verify_message(data)
            if not payload:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error_code": "not_authorized",
                    "message": "Invalid signature or not authorized"
                }))
                log.error(f"Message verification failed for type: {msg_type}")
                return

            # Verify the message type matches the JWS payload
            if payload.get("type") != msg_type:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error_code": "type_mismatch",
                    "message": "Message type mismatch"
                }))
                log.error(f"Type mismatch: expected {msg_type}, got {payload.get('type')}")
                return

            # Handle different message types
            if msg_type == "state":
                await self._handle_state_update(data)
            elif msg_type == "heartbeat":
                # Handle state update from heartbeat data
                await self._handle_state_update(data)

                # Respond to heartbeat (no signature needed for ack)
                response = {
                    "type": "heartbeat_ack"
                }
                await websocket.send(json.dumps(response))
            elif msg_type == "command_response":
                # Extension acknowledged command
                log.debug(f"Command response: {data}")
            else:
                log.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError:
            log.error("Invalid JSON received")
        except Exception as e:
            log.error(f"Error handling message: {e}")

    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """Handle client connection"""
        client_addr = websocket.remote_address
        log.info(f"Client connected: {client_addr}")

        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            log.info(f"Client disconnected: {client_addr}")
        finally:
            # Clean up connection
            if self.active_connection == websocket:
                self.active_connection = None
                self.extension_id = None
                self.instance_id = None
                self.connected = False

                # Reset state
                self.current_state = {
                    "mic_enabled": False,
                    "camera_enabled": False,
                    "hand_raised": False,
                    "in_meeting": False,
                    "meeting_id": None,
                    "meeting_name": None,
                    "participant_count": 0,
                }
                self._notify_state_update()

    async def send_command(self, action: str, data: Optional[Dict] = None) -> bool:
        """
        Send command to extension.
        Returns True if sent successfully, False otherwise.
        """
        if not self.active_connection:
            log.warning("Cannot send command: no active connection")
            return False

        try:
            # Send command message (no signature needed from server)
            command = {
                "type": "command",
                "action": action,
                "data": data or {}
            }

            await self.active_connection.send(json.dumps(command))
            log.debug(f"Command sent: {action}")
            return True
        except Exception as e:
            log.error(f"Error sending command: {e}")
            return False

    async def _run_server(self):
        """Run WebSocket server"""
        try:
            async with websockets.serve(self._handle_client, self.host, self.port):
                log.info(f"WebSocket server started on {self.host}:{self.port}")
                await asyncio.Future()  # Run forever
        except Exception as e:
            log.error(f"Server error: {e}")

    def start(self):
        """Start WebSocket server in background thread"""
        if self.loop and self.loop.is_running():
            log.warning("Server already running")
            return

        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._run_server())

        import threading
        thread = threading.Thread(target=run_loop, daemon=True, name="google_meet_ws_server")
        thread.start()
        log.info("WebSocket server thread started")

    def stop(self):
        """Stop WebSocket server"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop = None
        log.info("WebSocket server stopped")

    def get_state(self) -> Dict[str, Any]:
        """Get current meeting state"""
        return self.current_state.copy()

    def is_connected(self) -> bool:
        """Check if extension is connected"""
        return self.connected

    # Command methods (to be called by Backend)

    def toggle_microphone(self):
        """Toggle microphone in meeting"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.send_command("toggle_mic"),
                self.loop
            )

    def toggle_camera(self):
        """Toggle camera in meeting"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.send_command("toggle_camera"),
                self.loop
            )

    def toggle_hand(self):
        """Toggle raised hand in meeting"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.send_command("toggle_hand"),
                self.loop
            )

    def send_reaction(self, reaction: str):
        """Send reaction in meeting"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.send_command("send_reaction", {"reaction": reaction}),
                self.loop
            )

    def leave_call(self):
        """Leave the current meeting"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self.send_command("leave_call"),
                self.loop
            )

    # Pairing management methods (for UI)

    def get_pending_pairing_requests(self) -> list[PairingRequest]:
        """Get all pending pairing requests for UI display"""
        return self.pairing.get_pending_requests()

    def get_authorized_instances(self) -> list[PairingRequest]:
        """Get all authorized instances"""
        return self.pairing.get_authorized_instances()
