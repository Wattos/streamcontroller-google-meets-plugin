"""
ToggleCamera - Toggle camera in Google Meet
"""

from .ToggleStateAction import ToggleStateAction


class ToggleCamera(ToggleStateAction):
    """Action to toggle camera in Google Meet"""

    # Configuration for ToggleStateAction
    IMAGE_NAME_ON = "camera_on"
    IMAGE_NAME_OFF = "camera_off"
    BACKEND_STATE_METHOD = "get_camera_enabled"
    BACKEND_TOGGLE_METHOD = "toggle_camera"
    LABEL_ON = ""
    LABEL_OFF = ""
