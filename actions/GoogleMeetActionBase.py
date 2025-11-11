from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page

# Import gtk modules
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

import threading
import os
from loguru import logger as log
from .ImageManager import ImageManager, ImageMode


class GoogleMeetActionBase(ActionBase):
    """Base class for all Google Meet actions"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.has_configuration = True

        # Connection status label
        self.status_label = Gtk.Label(
            label="No Connection",
            css_classes=["bold", "red"]
        )

        # Track approval UI rows
        self.approval_rows = []

        # State caching for preventing unnecessary re-renders
        self._cached_state = None

    def get_connected(self) -> bool:
        """Check if extension is connected"""
        try:
            if self.plugin_base.backend is None:
                return False
            return self.plugin_base.backend.get_connected()
        except Exception as e:
            log.error(f"Error checking connection: {e}")
            return False

    def get_in_meeting(self) -> bool:
        """Check if currently in a meeting"""
        try:
            if self.plugin_base.backend is None:
                return False
            return self.plugin_base.backend.get_in_meeting() or False
        except Exception as e:
            log.error(f"Error checking meeting status: {e}")
            return False

    def get_config_rows(self) -> list:
        """Get configuration rows for this action"""
        rows = []

        # WebSocket settings
        self.port_spinner = Adw.SpinRow.new_with_range(1024, 65535, 1)
        self.port_spinner.set_title("WebSocket Port")
        rows.append(self.port_spinner)

        # Extension approval section
        self.approval_expander = Adw.ExpanderRow()
        self.approval_expander.set_title("Extension Approvals")
        self.approval_expander.set_subtitle("Manage browser extension connections")

        # Add refresh button
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", self.on_refresh_approvals)
        refresh_button.set_valign(Gtk.Align.CENTER)
        self.approval_expander.add_suffix(refresh_button)

        rows.append(self.approval_expander)

        self.load_config_defaults()

        # Connect signals
        self.port_spinner.connect("notify::value", self.on_change_port)

        # Load approval UI
        self.refresh_approval_ui()

        return rows

    def load_config_defaults(self):
        """Load default configuration from plugin settings"""
        settings = self.plugin_base.get_settings()
        port = settings.setdefault("websocket_port", 8765)

        # Update UI
        self.port_spinner.set_value(port)
        self.update_status_label()

    def on_change_port(self, spinner, *args):
        """Handle port change"""
        settings = self.plugin_base.get_settings()
        new_port = int(spinner.get_value())
        settings["websocket_port"] = new_port
        self.plugin_base.set_settings(settings)

        # Update backend
        threading.Thread(
            target=self._update_websocket_settings,
            daemon=True,
            name="update_websocket_settings"
        ).start()

    def _update_websocket_settings(self):
        """Update WebSocket settings in backend"""
        try:
            settings = self.plugin_base.get_settings()
            host = settings.get("websocket_host", "127.0.0.1")
            port = settings.get("websocket_port", 8765)

            self.plugin_base.backend.update_websocket_settings(host, port)
            self.update_status_label()
        except Exception as e:
            log.error(f"Error updating WebSocket settings: {e}")

    def update_status_label(self) -> None:
        """Update connection status label"""
        threading.Thread(
            target=self._update_status_label,
            daemon=True,
            name="update_status_label"
        ).start()

    def _update_status_label(self):
        """Update status label (thread-safe)"""
        try:
            if self.get_connected():
                self.status_label.set_label("Connected")
                self.status_label.remove_css_class("red")
                self.status_label.add_css_class("green")
            else:
                self.status_label.set_label("No Connection")
                self.status_label.remove_css_class("green")
                self.status_label.add_css_class("red")
        except Exception as e:
            log.error(f"Error updating status label: {e}")

    def get_custom_config_area(self):
        """Get custom configuration area widget"""
        self.update_status_label()
        return self.status_label

    def on_refresh_approvals(self, button=None):
        """Refresh approval UI"""
        self.refresh_approval_ui()

    def refresh_approval_ui(self):
        """Refresh the approval management UI"""
        if not hasattr(self, 'approval_expander'):
            return

        try:
            # Clear existing rows
            for row in self.approval_rows:
                self.approval_expander.remove(row)
            self.approval_rows.clear()

            # Get pending and approved pairing requests
            pending = []
            approved = []

            if self.plugin_base.backend is not None:
                try:
                    pending = self.plugin_base.backend.get_pending_pairing_requests()
                    approved = self.plugin_base.backend.get_authorized_instances()
                except Exception as e:
                    log.error(f"Error getting pairing requests: {e}")

            # Add pending approvals
            if pending:
                pending_label = Adw.ActionRow()
                pending_label.set_title("Pending Pairing Requests")
                pending_label.set_title_lines(1)
                self.approval_expander.add_row(pending_label)
                self.approval_rows.append(pending_label)

                for request in pending:
                    metadata = request.metadata

                    # Build title from metadata
                    extension_name = metadata.get('extension_name', 'Unknown Extension')
                    browser_name = metadata.get('browser_name', 'Unknown Browser')
                    browser_version = metadata.get('browser_version', '')

                    title = f"{extension_name} ({browser_name}"
                    if browser_version:
                        title += f" {browser_version}"
                    title += ")"

                    # Build subtitle with OS and instance info
                    os_name = metadata.get('os', 'Unknown OS')
                    instance_short = request.instance_id[:8] if request.instance_id else 'Unknown'
                    subtitle = f"{os_name} • Instance: {instance_short}"

                    row = Adw.ActionRow()
                    row.set_title(title)
                    row.set_subtitle(subtitle)
                    row.set_title_lines(2)

                    # Approve button
                    approve_btn = Gtk.Button(label="Approve")
                    approve_btn.add_css_class("suggested-action")
                    approve_btn.set_valign(Gtk.Align.CENTER)
                    approve_btn.connect("clicked", self.on_approve_instance,
                                      request.extension_id, request.instance_id)
                    row.add_suffix(approve_btn)

                    # Deny button
                    deny_btn = Gtk.Button(label="Deny")
                    deny_btn.add_css_class("destructive-action")
                    deny_btn.set_valign(Gtk.Align.CENTER)
                    deny_btn.connect("clicked", self.on_deny_instance,
                                    request.extension_id, request.instance_id)
                    row.add_suffix(deny_btn)

                    self.approval_expander.add_row(row)
                    self.approval_rows.append(row)

            # Add approved instances
            if approved:
                approved_label = Adw.ActionRow()
                approved_label.set_title("Authorized Instances")
                approved_label.set_title_lines(1)
                self.approval_expander.add_row(approved_label)
                self.approval_rows.append(approved_label)

                for request in approved:
                    metadata = request.metadata

                    # Build title from metadata
                    extension_name = metadata.get('extension_name', 'Unknown Extension')
                    browser_name = metadata.get('browser_name', 'Unknown Browser')
                    browser_version = metadata.get('browser_version', '')

                    title = f"{extension_name} ({browser_name}"
                    if browser_version:
                        title += f" {browser_version}"
                    title += ")"

                    # Build subtitle with OS and instance info
                    os_name = metadata.get('os', 'Unknown OS')
                    instance_short = request.instance_id[:8] if request.instance_id else 'Unknown'
                    subtitle = f"{os_name} • Instance: {instance_short}"

                    row = Adw.ActionRow()
                    row.set_title(title)
                    row.set_subtitle(subtitle)
                    row.set_title_lines(2)

                    # Revoke button
                    revoke_btn = Gtk.Button(label="Revoke")
                    revoke_btn.add_css_class("destructive-action")
                    revoke_btn.set_valign(Gtk.Align.CENTER)
                    revoke_btn.connect("clicked", self.on_revoke_instance,
                                      request.extension_id, request.instance_id)
                    row.add_suffix(revoke_btn)

                    self.approval_expander.add_row(row)
                    self.approval_rows.append(row)

            # If nothing to show
            if not pending and not approved:
                empty_row = Adw.ActionRow()
                empty_row.set_title("No extensions")
                empty_row.set_subtitle("Extensions will appear here when they connect")
                empty_row.set_title_lines(1)
                self.approval_expander.add_row(empty_row)
                self.approval_rows.append(empty_row)

        except Exception as e:
            log.error(f"Error refreshing approval UI: {e}")

    def on_approve_instance(self, button, extension_id, instance_id):
        """Approve an instance"""
        try:
            if self.plugin_base.backend is not None:
                self.plugin_base.backend.approve_instance(extension_id, instance_id)
                log.info(f"Approved instance: {extension_id}/{instance_id}")
                # Refresh UI after short delay
                threading.Thread(
                    target=self._delayed_refresh_approval_ui,
                    daemon=True,
                    name="refresh_approval_ui"
                ).start()
        except Exception as e:
            log.error(f"Error approving instance: {e}")

    def on_deny_instance(self, button, extension_id, instance_id):
        """Deny an instance"""
        try:
            if self.plugin_base.backend is not None:
                self.plugin_base.backend.deny_instance(extension_id, instance_id)
                log.info(f"Denied instance: {extension_id}/{instance_id}")
                # Refresh UI after short delay
                threading.Thread(
                    target=self._delayed_refresh_approval_ui,
                    daemon=True,
                    name="refresh_approval_ui"
                ).start()
        except Exception as e:
            log.error(f"Error denying instance: {e}")

    def on_revoke_instance(self, button, extension_id, instance_id):
        """Revoke an approved instance"""
        try:
            if self.plugin_base.backend is not None:
                self.plugin_base.backend.revoke_instance(extension_id, instance_id)
                log.info(f"Revoked instance: {extension_id}/{instance_id}")
                # Refresh UI after short delay
                threading.Thread(
                    target=self._delayed_refresh_approval_ui,
                    daemon=True,
                    name="refresh_approval_ui"
                ).start()
        except Exception as e:
            log.error(f"Error revoking instance: {e}")

    def _delayed_refresh_approval_ui(self):
        """Refresh approval UI after short delay"""
        import time
        time.sleep(0.2)
        from gi.repository import GLib
        GLib.idle_add(self.refresh_approval_ui)

    # ========================================
    # Image Access (delegates to ImageManager)
    # ========================================

    def get_image(self, name: str, connection_state: str = None, mode: ImageMode = None):
        """
        Get a preloaded image from ImageManager.

        Args:
            name: Image name (e.g., "mic_on", "reaction_thumbs_up")
            connection_state: Connection state ("connected", "disconnected", "not_in_meeting")
                             If provided, automatically determines mode
            mode: ImageMode.REGULAR (color) or ImageMode.DISABLED (grayscale)
                 If connection_state is provided, this is ignored

        Returns:
            PIL Image object or None if not found
        """
        # If connection_state is provided, determine mode automatically
        if connection_state is not None:
            if connection_state in ["disconnected", "not_in_meeting"]:
                mode = ImageMode.DISABLED
            else:
                mode = ImageMode.REGULAR
        # If mode is still None, default to REGULAR
        elif mode is None:
            mode = ImageMode.REGULAR

        return ImageManager.get_image(name, mode)

    # ========================================
    # Template Method Pattern for State Management
    # ========================================

    def compute_state(self) -> dict:
        """
        Compute action-specific state.
        Child classes override this to add their specific state data.

        Returns:
            Dictionary with action-specific state (empty by default)
        """
        return {}

    def render_state(self, state: dict, connection_state: str):
        """
        Render the action based on current state.
        Child classes must implement this to define their rendering logic.

        Args:
            state: Full state dictionary including connection_state and action-specific state
            connection_state: Current connection state ("connected", "disconnected", "not_in_meeting")
        """
        raise NotImplementedError("Child classes must implement render_state()")

    def update_state(self):
        """
        Update action state and render if changed.
        This method is called by on_tick() and handles:
        1. Getting connection/meeting status
        2. Calling compute_state() for action-specific state
        3. Comparing with cached state
        4. Calling render_state() if state changed
        """
        try:
            # Get connection and meeting status
            connected = self.get_connected()
            in_meeting = self.get_in_meeting()

            # Determine connection state
            if not connected:
                connection_state = "disconnected"
            elif not in_meeting:
                connection_state = "not_in_meeting"
            else:
                connection_state = "connected"

            # Create base state
            base_state = {
                "connection_state": connection_state,
                "connected": connected,
                "in_meeting": in_meeting
            }

            # Get action-specific state from child class
            child_state = self.compute_state()

            # Merge states
            full_state = {**base_state, **child_state}

            # Compare with cached state
            if full_state != self._cached_state:
                # State has changed, render it
                self.render_state(full_state, connection_state)
                # Update cache
                self._cached_state = full_state

        except Exception as e:
            log.error(f"Error updating state: {e}")

    def on_ready(self):
        """
        Called when action becomes ready (e.g., page loads).
        Clears cached state to force a fresh render.
        """
        self._cached_state = None
        self.update_state()

    def on_tick(self):
        """
        Called periodically by StreamController.
        Updates the action state.
        """
        self.update_state()
