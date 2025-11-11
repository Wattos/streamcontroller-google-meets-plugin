"""
InMeetingStatus - Display meeting status (informational only)

Shows whether the user is currently in a Google Meet meeting.
This is a read-only action that does not perform any action when clicked.
"""

from .GoogleMeetActionBase import GoogleMeetActionBase


class InMeetingStatus(GoogleMeetActionBase):
    """Action to display meeting status (informational only)"""

    # No need to override compute_state() - base class already provides "in_meeting" state

    def render_state(self, state: dict, connection_state: str):
        """Render meeting status display"""
        in_meeting = state.get("in_meeting", False)

        # Get image based on meeting status
        img = self.get_image("in_meeting", connection_state)
        if img:
            self.set_media(image=img, size=0.90)

        # Set label based on meeting status
        if in_meeting:
            self.set_bottom_label("IN MEETING", font_size=11)
        else:
            self.set_bottom_label("NOT IN MEETING", font_size=10)

    def on_key_down(self):
        """Called when button is pressed - does nothing (informational only)"""
        pass
