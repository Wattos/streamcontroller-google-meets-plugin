"""
ToggleStateAction - Base class for toggle actions (Mic, Camera, Hand)

Provides common implementation for actions that toggle between ON/OFF states
with automatic state synchronization from the backend.
"""

import threading
from .GoogleMeetActionBase import GoogleMeetActionBase
from .ImageManager import ImageMode
from .mixins import ToggleMixin, State
from loguru import logger as log


class ToggleStateAction(ToggleMixin, GoogleMeetActionBase):
    """
    Base class for toggle actions with state synchronization.

    Subclasses must define these class attributes:
    - IMAGE_NAME_ON: str - Image name for ON state (e.g., "mic_on")
    - IMAGE_NAME_OFF: str - Image name for OFF state (e.g., "mic_off")
    - BACKEND_STATE_METHOD: str - Backend method name to query state (e.g., "get_mic_enabled")
    - BACKEND_TOGGLE_METHOD: str - Backend method name to toggle (e.g., "toggle_microphone")
    - LABEL_ON: str - Label text for ON state (e.g., "ON")
    - LABEL_OFF: str - Label text for OFF state (e.g., "OFF")
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
        self.current_state = State.UNKNOWN

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

    def on_ready(self):
        """Called when action is ready"""
        self.current_state = State.UNKNOWN

    def update_state(self):
        """Update button state based on backend state"""
        if not self.get_connected() or not self.get_in_meeting():
            self.current_state = State.UNKNOWN
            # Show grayed-out icon when disconnected
            disconnected_img = self.get_image(self.IMAGE_NAME_ON, ImageMode.DISABLED)
            self.set_media(image=disconnected_img, size=0.9)
            return

        try:
            # Query state from backend using configured method
            backend_method = getattr(self.plugin_base.backend, self.BACKEND_STATE_METHOD)
            state_enabled = backend_method()

            if state_enabled is None:
                self.current_state = State.UNKNOWN
                self.show_error()
                return

            new_state = State.ENABLED if state_enabled else State.DISABLED
            self.show_for_state(new_state)
        except Exception as e:
            log.error(f"Error updating {self.__class__.__name__} state: {e}")
            self.current_state = State.UNKNOWN
            self.show_error()

    def show_for_state(self, state: State):
        """Update button appearance for given state"""
        if state == self.current_state:
            return

        self.current_state = state

        # Set icon from preloaded images
        if state == State.ENABLED:
            img = self.get_image(self.IMAGE_NAME_ON)
            if img:
                self.set_media(image=img, size=0.9)

            if (self.LABEL_ON):
                self.set_bottom_label(self.LABEL_ON, font_size=14)

        elif state == State.DISABLED:
            img = self.get_image(self.IMAGE_NAME_OFF)
            if img:
                self.set_media(image=img, size=0.9)

            if (self.LABEL_OFF):
                self.set_bottom_label(self.LABEL_OFF, font_size=14)
        else:
            img = self.get_image("error")
            if img:
                self.set_media(image=img, size=0.9)
            self.set_bottom_label("", font_size=14)

    def on_key_down(self):
        """Called when button is pressed"""
        if not self.get_connected() or not self.get_in_meeting():
            self.show_error()
            return

        try:
            # Toggle using configured backend method
            backend_method = getattr(self.plugin_base.backend, self.BACKEND_TOGGLE_METHOD)
            backend_method()
            self.update_state()
            
        except Exception as e:
            log.error(f"Error toggling {self.__class__.__name__}: {e}")
            self.show_error()

    def on_tick(self):
        """Called periodically to update state"""
        self.update_state()
