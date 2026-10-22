"""윈도우 입력 상태 감지. 다른 운영체제에서는 전역 Shift 메뉴만 비활성화합니다."""
from dataclasses import dataclass
import ctypes
import sys
import time


@dataclass(frozen=True)
class InputState:
    primary: bool = False
    shift: bool = False
    escape: bool = False
    position: tuple[int, int] | None = None


class WindowsInput:
    supported = sys.platform == "win32"

    def __init__(self):
        if not self.supported:
            return
        from ctypes import wintypes
        self.point_type = wintypes.POINT
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
        self.user32.GetAsyncKeyState.restype = ctypes.c_short
        self.user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        self.user32.GetSystemMetrics.restype = ctypes.c_int
        self.user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        self.user32.GetCursorPos.restype = wintypes.BOOL

    def read(self) -> InputState:
        if not self.supported:
            return InputState()
        primary_key = 0x02 if self.user32.GetSystemMetrics(23) else 0x01
        point = self.point_type()
        position = (point.x, point.y) if self.user32.GetCursorPos(ctypes.byref(point)) else None
        return InputState(self.user32.GetAsyncKeyState(primary_key) < 0,
                          self.user32.GetAsyncKeyState(0x10) < 0,
                          self.user32.GetAsyncKeyState(0x1B) < 0, position)


class GestureState:
    """윈도우 API와 분리하여 테스트할 수 있는 입력 상태 기계입니다."""
    def __init__(self):
        self.previous = InputState()
        self.start = None
        self.released_at = None

    def update(self, state: InputState, visible: bool, enabled: bool, now: float | None = None) -> str:
        now = time.monotonic() if now is None else now
        if state.primary and not self.previous.primary:
            self.start = state.position
        moved = (state.position is not None and self.start is not None
                 and sum((a - b) ** 2 for a, b in zip(state.position, self.start)) >= 64)
        action = ""
        if visible and (state.escape or not enabled):
            action = "hide"
        elif enabled and not visible and state.primary and self.previous.primary and moved and state.shift and not self.previous.shift:
            action = "show"
        if visible and not state.primary:
            if self.released_at is None:
                self.released_at = now
            elif now - self.released_at >= 0.3:
                action = "hide"
        else:
            self.released_at = None
        self.previous = state
        return action
