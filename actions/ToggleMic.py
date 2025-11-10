"""
ToggleMic - Toggle microphone in Google Meet
"""

from .ToggleStateAction import ToggleStateAction


class ToggleMic(ToggleStateAction):
    """Action to toggle microphone in Google Meet"""

    # Configuration for ToggleStateAction
    IMAGE_NAME_ON = "mic_on"
    IMAGE_NAME_OFF = "mic_off"
    BACKEND_STATE_METHOD = "get_mic_enabled"
    BACKEND_TOGGLE_METHOD = "toggle_microphone"
    LABEL_ON = ""
    LABEL_OFF = ""
