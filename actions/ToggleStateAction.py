"""
ToggleStateAction - Base class for toggle actions (Mic, Camera, Hand)

Provides common implementation for actions that toggle between ON/OFF states
with automatic state synchronization from the backend.
"""

from .GoogleMeetActionBase import GoogleMeetActionBase
from loguru import logger as log


class ToggleStateAction(GoogleMeetActionBase):
    """
    Base class for toggle actions with state synchronization.

    Subclasses must define these class attributes:
    - IMAGE_NAME_ON: str - Image name for ON state (e.g., "mic_on")
    - IMAGE_NAME_OFF: str - Image name for OFF state (e.g., "mic_off")
    - BACKEND_STATE_METHOD: str - Backend method name to query state (e.g., "get_mic_enabled")
    - BACKEND_TOGGLE_METHOD: str - Backend method name to toggle (e.g., "toggle_microphone")
    - LABEL_ON: str - Label text for ON state (e.g., "ON") - optional
    - LABEL_OFF: str - Label text for OFF state (e.g., "OFF") - optional
    """

    # Subclasses must override these
    IMAGE_NAME_ON = None
    IMAGE_NAME_OFF = None
    BACKEND_STATE_METHOD = None
    BACKEND_TOGGLE_METHOD = None
    LABEL_ON = None
    LABEL_OFF = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Validate configuration
        if not all([
            self.IMAGE_NAME_ON,
            self.IMAGE_NAME_OFF,
            self.BACKEND_STATE_METHOD,
            self.BACKEND_TOGGLE_METHOD
        ]):
            raise ValueError(
                f"{self.__class__.__name__} must define IMAGE_NAME_ON, IMAGE_NAME_OFF, "
                "BACKEND_STATE_METHOD, and BACKEND_TOGGLE_METHOD"
            )

    def compute_state(self) -> dict:
        """Get toggle state from backend"""
        try:
            if self.plugin_base.backend is None:
                return {"toggle_enabled": None}

            # Query state from backend using configured method
            backend_method = getattr(self.plugin_base.backend, self.BACKEND_STATE_METHOD)
            toggle_enabled = backend_method()
            return {"toggle_enabled": toggle_enabled}
        except Exception as e:
            log.error(f"Error getting {self.__class__.__name__} state: {e}")
            return {"toggle_enabled": None}

    def render_state(self, state: dict, connection_state: str):
        """Render toggle button based on state"""
        toggle_enabled = state.get("toggle_enabled")

        # Show error state if toggle state is unknown
        if toggle_enabled is None:
            img = self.get_image("error", connection_state)
            if img:
                self.set_media(image=img, size=0.9)
            return

        # Select appropriate image based on toggle state
        if toggle_enabled:
            img = self.get_image(self.IMAGE_NAME_ON, connection_state)
            label = self.LABEL_ON
        else:
            img = self.get_image(self.IMAGE_NAME_OFF, connection_state)
            label = self.LABEL_OFF

        # Set image
        if img:
            self.set_media(image=img, size=0.9)

        # Set label if provided
        if label:
            self.set_bottom_label(label, font_size=14)

    def on_key_down(self):
        """Toggle when button is pressed"""
        if not self.get_connected() or not self.get_in_meeting():
            return

        try:
            if self.plugin_base.backend is None:
                return

            # Toggle using configured backend method
            backend_method = getattr(self.plugin_base.backend, self.BACKEND_TOGGLE_METHOD)
            backend_method()
            # Force immediate state update
            self.update_state()
        except Exception as e:
            log.error(f"Error toggling {self.__class__.__name__}: {e}")
