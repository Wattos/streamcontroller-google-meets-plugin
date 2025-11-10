from .MixinBase import MixinBase, State


class ToggleMixin(MixinBase):
    """Mixin for toggle actions (on/off behavior)"""

    def next_state(self) -> State:
        """Toggle between ENABLED and DISABLED states"""
        match self.current_state:
            case State.UNKNOWN:
                raise ValueError("Cannot toggle from UNKNOWN state")
            case State.DISABLED:
                return State.ENABLED
            case State.ENABLED:
                return State.DISABLED
