# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport

print("Launching Google Meet! - 0")
# Import gtk modules
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import sys
import os
from loguru import logger as log

# Add plugin to sys.paths
sys.path.append(os.path.dirname(__file__))

# Import actions
from actions.ToggleMic import ToggleMic
from actions.ToggleCamera import ToggleCamera
from actions.RaiseHand import RaiseHand
from actions.SendReaction import SendReaction
from actions.InMeetingStatus import InMeetingStatus
from actions.ParticipantCount import ParticipantCount
from actions.LeaveCall import LeaveCall
from actions.ImageManager import ImageManager

print("Launching Google Meet! - 1")
class GoogleMeetPlugin(PluginBase):
    def __init__(self):
        super().__init__()

        # Initialize ImageManager with all plugin images
        log.info("Initializing ImageManager...")
        ImageManager.initialize(os.path.join(self.PATH, "assets"))
        log.info("ImageManager initialized")

        # Launch backend
        log.info("Launching Google Meet backend...")

        self.launch_backend(
            os.path.join(self.PATH, "backend", "backend.py"),
            os.path.join(self.PATH, "backend", ".venv"),
            open_in_terminal=False,
        )
        log.info("Google Meet backend launched")

        # Register actions
        toggle_mic_holder = ActionHolder(
            plugin_base=self,
            action_base=ToggleMic,
            action_id_suffix="ToggleMic",
            action_name="Toggle Microphone",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED,
            },
        )
        self.add_action_holder(toggle_mic_holder)

        toggle_camera_holder = ActionHolder(
            plugin_base=self,
            action_base=ToggleCamera,
            action_id_suffix="ToggleCamera",
            action_name="Toggle Camera",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED,
            },
        )
        self.add_action_holder(toggle_camera_holder)

        raise_hand_holder = ActionHolder(
            plugin_base=self,
            action_base=RaiseHand,
            action_id_suffix="RaiseHand",
            action_name="Raise Hand",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED,
            },
        )
        self.add_action_holder(raise_hand_holder)

        send_reaction_holder = ActionHolder(
            plugin_base=self,
            action_base=SendReaction,
            action_id_suffix="SendReaction",
            action_name="Send Reaction",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.UNTESTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED,
            },
        )
        self.add_action_holder(send_reaction_holder)

        in_meeting_status_holder = ActionHolder(
            plugin_base=self,
            action_base=InMeetingStatus,
            action_id_suffix="InMeetingStatus",
            action_name="Meeting Status",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED,
            },
        )
        self.add_action_holder(in_meeting_status_holder)

        participant_count_holder = ActionHolder(
            plugin_base=self,
            action_base=ParticipantCount,
            action_id_suffix="ParticipantCount",
            action_name="Participant Count",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED,
            },
        )
        self.add_action_holder(participant_count_holder)

        leave_call_holder = ActionHolder(
            plugin_base=self,
            action_base=LeaveCall,
            action_id_suffix="LeaveCall",
            action_name="Leave Call",
            action_support={
                Input.Key: ActionInputSupport.SUPPORTED,
                Input.Dial: ActionInputSupport.SUPPORTED,
                Input.Touchscreen: ActionInputSupport.SUPPORTED,
            },
        )
        self.add_action_holder(leave_call_holder)

        # Register plugin
        self.register(
            plugin_name="Google Meet Controller",
            github_repo="https://github.com/Wattos/streamcontroller-google-meets-plugin",
            plugin_version="1.0.0",
            app_version="1.5.0-beta.11"
        )



    def get_connected(self):
        """Check if extension is connected"""
        try:
            return self.backend.get_connected()
        except Exception as e:
            log.error(e)
            return False