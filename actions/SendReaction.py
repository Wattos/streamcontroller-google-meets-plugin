import threading
from .GoogleMeetActionBase import GoogleMeetActionBase
from .ImageManager import ImageMode
from loguru import logger as log

# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw


class SendReaction(GoogleMeetActionBase):
    """Action to send reactions in Google Meet"""

    # Available reactions
    REACTIONS = {
        "sparkling_heart": "💖",
        "thumbs_up": "👍",
        "celebrate": "🎉",
        "applause": "👏",
        "laugh": "😂",
        "surprised": "😮",
        "sad": "😢",
        "thinking": "🤔",
        "thumbs_down": "👎",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self):
        settings = self.get_settings()
        self.reaction = settings.get("reaction", "thumbs_up")

        """Called when action is ready"""
        # Set icon based on selected reaction
        self.update_icon()

    def update_icon(self):
        """Update button icon based on selected reaction"""
        reaction_name = self.reaction

        if not self.get_connected() or not self.get_in_meeting():
            # Show grayed-out reaction icon when disconnected
            disconnected_img = self.get_image(f"reaction_{self.reaction}", ImageMode.DISABLED)
            self.set_media(image=disconnected_img, size=0.8)
            return

        img = self.get_image(f"reaction_{reaction_name}")
        self.set_media(image=img, size=0.8)

    def on_key_down(self):
        """Called when button is pressed"""
        if not self.get_in_meeting():
            # Show error for "no meeting" state
            self.show_error(duration=2.0)
            return

        try:
            # Send reaction
            self.plugin_base.backend.send_reaction(self.reaction)
        except Exception as e:
            log.error(f"Error sending reaction: {e}")
            self.show_error(duration=3.0)

    def get_config_rows(self) -> list:
        """Get configuration rows"""
        super_rows = super().get_config_rows()

        # Reaction selector
        self.reaction_model = Gtk.StringList()
        for reaction_id, reaction_name in self.REACTIONS.items():
            self.reaction_model.append(reaction_name)

        self.reaction_row = Adw.ComboRow(
            model=self.reaction_model,
            title="Reaction"
        )

        # Load current selection
        self.load_reaction_config()

        # Connect signal
        self.reaction_row.connect("notify::selected", self.on_reaction_changed)

        super_rows.append(self.reaction_row)
        return super_rows

    def load_reaction_config(self):
        """Load reaction configuration"""
        reaction = self.get_settings().get("reaction", "thumbs_up")

        # Find index in REACTIONS
        reaction_ids = list(self.REACTIONS.keys())
        if reaction in reaction_ids:
            index = reaction_ids.index(reaction)
            self.reaction_row.set_selected(index)

    def on_reaction_changed(self, row, *args):
        """Handle reaction change"""
        selected_index = row.get_selected()
        reaction_ids = list(self.REACTIONS.keys())

        if 0 <= selected_index < len(reaction_ids):
            self.reaction = reaction_ids[selected_index]

            # Save to settings
            settings = self.get_settings()
            settings["reaction"] = self.reaction
            self.set_settings(settings)

            # Update icon
            self.update_icon()
    
    def on_tick(self):
        """Called periodically to update state"""
        self.update_icon()
