"""
ParticipantCount - Display participant count (informational only)

Shows the number of participants currently in the Google Meet meeting.
This is a read-only action that does not perform any action when clicked.
"""

from .GoogleMeetActionBase import GoogleMeetActionBase
from loguru import logger as log


class ParticipantCount(GoogleMeetActionBase):
    """Action to display participant count (informational only)"""

    def compute_state(self) -> dict:
        """Get participant count from backend"""
        try:
            if self.plugin_base.backend is None:
                return {"participant_count": None}

            count = self.plugin_base.backend.get_participant_count()
            return {"participant_count": count}
        except Exception as e:
            log.error(f"Error getting participant count: {e}")
            return {"participant_count": None}

    def render_state(self, state: dict, connection_state: str):
        """Render participant count display"""
        count = state.get("participant_count")

        # Show error state if count is unknown
        if count is None:
            img = self.get_image("error", connection_state)
            if img:
                self.set_media(image=img, size=0.90)
            self.set_bottom_label("--", font_size=22)
            return

        # Show participant count
        img = self.get_image("participants", connection_state)
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

    def on_key_down(self):
        """Called when button is pressed - does nothing (informational only)"""
        pass
