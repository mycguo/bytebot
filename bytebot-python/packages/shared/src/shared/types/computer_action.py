"""Computer action types for desktop control."""

from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    """Screen coordinates."""
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")


Button = Literal["left", "right", "middle"]
Press = Literal["up", "down"]
Application = Literal[
    "firefox", "1password", "thunderbird", "vscode", "terminal", "desktop", "directory"
]


class MoveMouseAction(BaseModel):
    """Move mouse to specific coordinates."""
    action: Literal["move_mouse"]
    coordinates: Coordinates


class TraceMouseAction(BaseModel):
    """Trace mouse along a path."""
    action: Literal["trace_mouse"]
    path: List[Coordinates]
    holdKeys: Optional[List[str]] = None


class ClickMouseAction(BaseModel):
    """Click mouse at coordinates."""
    action: Literal["click_mouse"]
    coordinates: Optional[Coordinates] = None
    button: Button
    holdKeys: Optional[List[str]] = None
    clickCount: int = Field(default=1, description="Number of clicks")


class PressMouseAction(BaseModel):
    """Press or release mouse button."""
    action: Literal["press_mouse"]
    coordinates: Optional[Coordinates] = None
    button: Button
    press: Press


class DragMouseAction(BaseModel):
    """Drag mouse along a path."""
    action: Literal["drag_mouse"]
    path: List[Coordinates]
    button: Button
    holdKeys: Optional[List[str]] = None


class ScrollAction(BaseModel):
    """Scroll at coordinates."""
    action: Literal["scroll"]
    coordinates: Optional[Coordinates] = None
    direction: Literal["up", "down", "left", "right"]
    scrollCount: int = Field(default=1, description="Number of scroll steps")
    holdKeys: Optional[List[str]] = None


class TypeKeysAction(BaseModel):
    """Type specific keys with optional delay."""
    action: Literal["type_keys"]
    keys: List[str]
    delay: Optional[int] = None


class PasteTextAction(BaseModel):
    """Paste text from clipboard."""
    action: Literal["paste_text"]
    text: str


class PressKeysAction(BaseModel):
    """Press or release specific keys."""
    action: Literal["press_keys"]
    keys: List[str]
    press: Press


class TypeTextAction(BaseModel):
    """Type text with optional delay and sensitivity flag."""
    action: Literal["type_text"]
    text: str
    delay: Optional[int] = None
    sensitive: Optional[bool] = Field(default=False, description="Contains sensitive information")


class WaitAction(BaseModel):
    """Wait for specified duration."""
    action: Literal["wait"]
    duration: int = Field(..., description="Duration in milliseconds")


class ScreenshotAction(BaseModel):
    """Take a screenshot."""
    action: Literal["screenshot"]


class CursorPositionAction(BaseModel):
    """Get current cursor position."""
    action: Literal["cursor_position"]


class ApplicationAction(BaseModel):
    """Launch or interact with application."""
    action: Literal["application"]
    application: Application


class WriteFileAction(BaseModel):
    """Write data to file."""
    action: Literal["write_file"]
    path: str
    data: str = Field(..., description="Base64 encoded data")


class ReadFileAction(BaseModel):
    """Read file contents."""
    action: Literal["read_file"]
    path: str


# Union type for all computer actions
ComputerAction = Union[
    MoveMouseAction,
    TraceMouseAction,
    ClickMouseAction,
    PressMouseAction,
    DragMouseAction,
    ScrollAction,
    TypeKeysAction,
    PressKeysAction,
    TypeTextAction,
    PasteTextAction,
    WaitAction,
    ScreenshotAction,
    CursorPositionAction,
    ApplicationAction,
    WriteFileAction,
    ReadFileAction,
]