import logging
from typing import Dict, Optional, Any

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.ERROR)

from streamcontroller_plugin_tools import BackendBase
from GoogleMeetsController import GoogleMeetsController


class Backend(BackendBase):
    """
    Backend wrapper for Google Meet Controller.

    Provides clean API for StreamController actions to interact with
    Google Meet extension via WebSocket controller.
    """

    def __init__(self):
        super().__init__()

        # Get settings
        settings = self.frontend.get_settings()
        host = settings.get("websocket_host", "127.0.0.1")
        port = settings.get("websocket_port", 8765)

        # Initialize controller
        self.controller = GoogleMeetsController(host=host, port=port)

        # Start WebSocket server
        self.controller.start()
        print("Controller started")

        LOG.info("Google Meet Backend initialized")

    def get_connected(self) -> bool:
        """Check if extension is connected"""
        return self.controller.is_connected()

    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current meeting state"""
        try:
            return self.controller.get_state()
        except Exception as e:
            LOG.error(f"Error getting state: {e}")
            return None

    def get_mic_enabled(self) -> Optional[bool]:
        """Get microphone state"""
        state = self.get_state()
        if state:
            return state.get("mic_enabled", False)
        return None

    def get_camera_enabled(self) -> Optional[bool]:
        """Get camera state"""
        state = self.get_state()
        if state:
            return state.get("camera_enabled", False)
        return None

    def get_hand_raised(self) -> Optional[bool]:
        """Get raised hand state"""
        state = self.get_state()
        if state:
            return state.get("hand_raised", False)
        return None

    def get_in_meeting(self) -> Optional[bool]:
        """Check if currently in a meeting"""
        state = self.get_state()
        if state:
            return state.get("in_meeting", False)
        return None

    def get_participant_count(self) -> Optional[int]:
        """Get number of participants in the meeting"""
        state = self.get_state()
        if state:
            return state.get("participant_count", 0)
        return None

    def toggle_microphone(self) -> bool:
        """
        Toggle microphone in meeting.
        Returns True if command sent successfully.
        """
        try:
            self.controller.toggle_microphone()
            return True
        except Exception as e:
            LOG.error(f"Error toggling microphone: {e}")
            return False

    def toggle_camera(self) -> bool:
        """
        Toggle camera in meeting.
        Returns True if command sent successfully.
        """
        try:
            self.controller.toggle_camera()
            return True
        except Exception as e:
            LOG.error(f"Error toggling camera: {e}")
            return False

    def toggle_hand(self) -> bool:
        """
        Toggle raised hand in meeting.
        Returns True if command sent successfully.
        """
        try:
            self.controller.toggle_hand()
            return True
        except Exception as e:
            LOG.error(f"Error toggling hand: {e}")
            return False

    def send_reaction(self, reaction: str) -> bool:
        """
        Send reaction in meeting.

        Args:
            reaction: Reaction type (thumbs_up, heart, laugh, etc.)

        Returns:
            True if command sent successfully.
        """
        try:
            self.controller.send_reaction(reaction)
            return True
        except Exception as e:
            LOG.error(f"Error sending reaction: {e}")
            return False

    def leave_call(self) -> bool:
        """
        Leave the current meeting.
        Returns True if command sent successfully.
        """
        try:
            self.controller.leave_call()
            return True
        except Exception as e:
            LOG.error(f"Error leaving call: {e}")
            return False

    def get_authorized_instances(self):
        """Get list of authorized instances"""
        return self.controller.get_authorized_instances()

    def approve_instance(self, extension_id: str, instance_id: str):
        """Approve an instance"""
        self.controller.approve_instance(extension_id, instance_id)

    def deny_instance(self, extension_id: str, instance_id: str):
        """Deny an instance"""
        self.controller.deny_instance(extension_id, instance_id)

    def revoke_instance(self, extension_id: str, instance_id: str):
        """Revoke an authorized instance"""
        self.controller.revoke_instance(extension_id, instance_id)

    def get_pending_pairing_requests(self):
        """Get list of pending pairing requests"""
        return self.controller.get_pending_pairing_requests()

    def update_websocket_settings(self, host: str, port: int):
        """Update WebSocket server settings (requires restart)"""
        # Stop current server
        self.controller.stop()

        # Create new controller with new settings
        self.controller = GoogleMeetsController(host=host, port=port)

        # Start new server
        self.controller.start()

        LOG.info(f"WebSocket server restarted on {host}:{port}")

    def get_controller(self) -> GoogleMeetsController:
        """
        Get controller instance for advanced usage.
        Warning: Calling methods on the returned controller may raise Pyro errors.
        """
        return self.controller


# Create backend instance
backend = Backend()
