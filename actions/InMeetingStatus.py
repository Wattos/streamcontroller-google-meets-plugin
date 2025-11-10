"""
InMeetingStatus - Display meeting status (informational only)

Shows whether the user is currently in a Google Meet meeting.
This is a read-only action that does not perform any action when clicked.
"""

from .GoogleMeetActionBase import GoogleMeetActionBase
from .ImageManager import ImageMode
from loguru import logger as log


class InMeetingStatus(GoogleMeetActionBase):
    """Action to display meeting status (informational only)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        """Called when action is ready"""
        self.update_state()

    def update_state(self):
        """Update button display based on meeting status"""
        if not self.get_connected() or not self.get_in_meeting():
            # Not connected - show disabled
            self.show_not_in_meeting()
            return
            
        self.show_in_meeting()
           
    def show_in_meeting(self):
        """Show 'in meeting' state"""
        img = self.get_image("in_meeting", ImageMode.REGULAR)
        if img:
            self.set_media(image=img, size=0.90)
        self.set_bottom_label("IN MEETING", font_size=11)

    def show_not_in_meeting(self):
        """Show 'not in meeting' state"""
        img = self.get_image("in_meeting", ImageMode.DISABLED)
        if img:
            self.set_media(image=img, size=0.90)
        self.set_bottom_label("NOT IN MEETING", font_size=10)

    def show_error(self):
        """Show error state"""
        self.last_state = None
        img = self.get_image("error")
        if img:
            self.set_media(image=img, size=0.90)
        self.set_bottom_label("ERROR", font_size=12)

    def on_key_down(self):
        """Called when button is pressed - does nothing (informational only)"""
        pass

    def on_tick(self):
        """Called periodically to update state"""
        self.update_state()
