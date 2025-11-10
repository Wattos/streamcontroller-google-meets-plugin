"""
ParticipantCount - Display participant count (informational only)

Shows the number of participants currently in the Google Meet meeting.
This is a read-only action that does not perform any action when clicked.
"""

from .GoogleMeetActionBase import GoogleMeetActionBase
from .ImageManager import ImageMode
from loguru import logger as log


class ParticipantCount(GoogleMeetActionBase):
    """Action to display participant count (informational only)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_count = None

    def on_ready(self):
        """Called when action is ready"""
        self.last_count = None
        self.update_state()

    def update_state(self):
        """Update button display based on participant count"""
        if not self.get_connected() or not self.get_in_meeting():
            # Not connected or not in meeting - show disabled
            self.show_disconnected()
            return

        try:
            # Get participant count from backend
            count = self.plugin_base.backend.get_participant_count()

            if count is None:
                self.show_disconnected()
                return

            # Update display if count changed
            if count != self.last_count:
                self.last_count = count
                self.show_count(count)

        except Exception as e:
            log.error(f"Error updating ParticipantCount: {e}")
            self.show_error()

    def show_count(self, count: int):
        """Show participant count"""
        img = self.get_image("participants", ImageMode.REGULAR)
        if img:
            self.set_media(image=img, size=0.75)

        # Format count as string
        count_str = str(count)

        # Adjust font size based on number length
        if count >= 1000:
            font_size = 16
        elif count >= 100:
            font_size = 18
        elif count >= 10:
            font_size = 20
        else:
            font_size = 22

        self.set_bottom_label(count_str, font_size=font_size)

    def show_disconnected(self):
        """Show disconnected/not in meeting state"""
        if not self.get_connected() or not self.get_in_meeting():
            img = self.get_image("participants", ImageMode.DISABLED)
        else:
            img = self.get_image("participants", ImageMode.REGULAR)

        self.set_media(image=img, size=0.90)
        if self.last_count is not None:
            self.last_count = None
            self.set_bottom_label("--", font_size=22)

    def show_error(self):
        """Show error state"""
        self.last_count = None
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
