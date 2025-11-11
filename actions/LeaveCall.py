"""
LeaveCall - Leave the current Google Meet call

Shows a button to leave the meeting. Only active when in a meeting.
"""

from .GoogleMeetActionBase import GoogleMeetActionBase
from loguru import logger as log


class LeaveCall(GoogleMeetActionBase):
    """Action to leave the current meeting"""

    # No need to override compute_state() - base class already provides connection/meeting state

    def render_state(self, state: dict, connection_state: str):
        """Render leave call button"""
        # Get leave button image
        img = self.get_image("leave", connection_state)
        if img:
            self.set_media(image=img, size=0.9)

    def on_key_down(self):
        """Called when button is pressed - leave the call"""
        if not self.get_connected() or not self.get_in_meeting():
            return

        try:
            # Leave the call
            self.plugin_base.backend.leave_call()
            log.info("Left meeting")
        except Exception as e:
            log.error(f"Error leaving call: {e}")
