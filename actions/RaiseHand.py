"""
RaiseHand - Raise/lower hand in Google Meet
"""

from .ToggleStateAction import ToggleStateAction


class RaiseHand(ToggleStateAction):
    """Action to raise/lower hand in Google Meet"""

    # Configuration for ToggleStateAction
    IMAGE_NAME_ON = "hand_raised"
    IMAGE_NAME_OFF = "hand_lowered"
    BACKEND_STATE_METHOD = "get_hand_raised"
    BACKEND_TOGGLE_METHOD = "toggle_hand"
    LABEL_ON = ""
    LABEL_OFF = ""
