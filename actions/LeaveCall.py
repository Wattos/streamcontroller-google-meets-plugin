"""
LeaveCall - Leave the current Google Meet call

Shows a button to leave the meeting. Only active when in a meeting.
"""

from .GoogleMeetActionBase import GoogleMeetActionBase
from .ImageManager import ImageMode
from loguru import logger as log


class LeaveCall(GoogleMeetActionBase):
    """Action to leave the current meeting"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        """Called when action is ready"""
        self.update_state()

    def update_state(self):
        if not self.get_connected() or not self.get_in_meeting():
            # Show grayed-out icon when disconnected
            disconnected_img = self.get_image("leave", ImageMode.DISABLED)
            self.set_media(image=disconnected_img, size=0.9)
            return

        img = self.get_image("leave", ImageMode.REGULAR)
        self.set_media(image=img, size=0.9)

    def on_key_down(self):
        """Called when button is pressed - leave the call"""
        if not self.get_connected() or not self.get_in_meeting():
            self.show_error(duration=1.0)
            return

        try:
            # Leave the call
            self.plugin_base.backend.leave_call()
            log.info("Left meeting")

        except Exception as e:
            log.error(f"Error leaving call: {e}")
            self.show_error(duration=1.0)

    def on_tick(self):
        """Called periodically to update state"""
        self.update_state()
