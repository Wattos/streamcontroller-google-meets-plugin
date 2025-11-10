from abc import ABC, abstractmethod
from enum import IntEnum
from loguru import logger as log


class State(IntEnum):
    """
    Enum for representing state of a Google Meet control.
    bool(value) provides expected semantics for DISABLED (False) and ENABLED (True).
    """

    UNKNOWN = -1
    DISABLED = 0
    ENABLED = 1


class MixinBase(ABC):
    """Base class for action mixins"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_state: State = State.UNKNOWN

    @property
    def current_state(self) -> State:
        return self._current_state

    @current_state.setter
    def current_state(self, val: int | State):
        if val not in State:
            log.warning(f"current_state setter called with non-State type {type(val)=} {val=}.")
            val = State(val)

        self._current_state = val

    @abstractmethod
    def next_state(self) -> State:
        """Return the next state for this action"""
        pass

    def mixin_config_rows(self) -> list:
        """Return additional config rows for this mixin"""
        return []
