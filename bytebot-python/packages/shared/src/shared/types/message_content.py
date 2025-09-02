"""Message content types for AI interactions."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

from .computer_action import Button, Coordinates, Press


class MessageContentType(str, Enum):
    """Types of message content blocks."""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"
    REDACTED_THINKING = "redacted_thinking"
    USER_ACTION = "user_action"


class MessageContentBlockBase(BaseModel):
    """Base type for message content blocks."""
    type: MessageContentType
    content: Optional[List['MessageContentBlock']] = None


class TextContentBlock(MessageContentBlockBase):
    """Text content block."""
    type: Literal[MessageContentType.TEXT]
    text: str


class ImageSource(BaseModel):
    """Image source data."""
    media_type: Literal["image/png"]
    type: Literal["base64"]
    data: str


class ImageContentBlock(MessageContentBlockBase):
    """Image content block."""
    type: Literal[MessageContentType.IMAGE]
    source: ImageSource


class DocumentSource(BaseModel):
    """Document source data."""
    type: Literal["base64"]
    media_type: str
    data: str


class DocumentContentBlock(MessageContentBlockBase):
    """Document content block."""
    type: Literal[MessageContentType.DOCUMENT]
    source: DocumentSource
    name: Optional[str] = None
    size: Optional[int] = None


class ThinkingContentBlock(MessageContentBlockBase):
    """Thinking content block."""
    type: Literal[MessageContentType.THINKING]
    thinking: str
    signature: str


class RedactedThinkingContentBlock(MessageContentBlockBase):
    """Redacted thinking content block."""
    type: Literal[MessageContentType.REDACTED_THINKING]
    data: str


class ToolUseContentBlock(MessageContentBlockBase):
    """Tool use content block."""
    type: Literal[MessageContentType.TOOL_USE]
    name: str
    id: str
    input: Dict[str, Any]


# Computer tool use blocks
class MoveMouseToolUseBlock(ToolUseContentBlock):
    """Move mouse tool use."""
    name: Literal["computer_move_mouse"]
    input: Dict[str, Any] = Field(..., description="Contains coordinates")


class TraceMouseToolUseBlock(ToolUseContentBlock):
    """Trace mouse tool use."""
    name: Literal["computer_trace_mouse"]
    input: Dict[str, Any] = Field(..., description="Contains path and optional holdKeys")


class ClickMouseToolUseBlock(ToolUseContentBlock):
    """Click mouse tool use."""
    name: Literal["computer_click_mouse"]
    input: Dict[str, Any] = Field(..., description="Contains coordinates, button, holdKeys, clickCount")


class PressMouseToolUseBlock(ToolUseContentBlock):
    """Press mouse tool use."""
    name: Literal["computer_press_mouse"]
    input: Dict[str, Any] = Field(..., description="Contains coordinates, button, press")


class DragMouseToolUseBlock(ToolUseContentBlock):
    """Drag mouse tool use."""
    name: Literal["computer_drag_mouse"]
    input: Dict[str, Any] = Field(..., description="Contains path, button, holdKeys")


class ScrollToolUseBlock(ToolUseContentBlock):
    """Scroll tool use."""
    name: Literal["computer_scroll"]
    input: Dict[str, Any] = Field(..., description="Contains coordinates, direction, scrollCount, holdKeys")


class TypeKeysToolUseBlock(ToolUseContentBlock):
    """Type keys tool use."""
    name: Literal["computer_type_keys"]
    input: Dict[str, Any] = Field(..., description="Contains keys and optional delay")


class PressKeysToolUseBlock(ToolUseContentBlock):
    """Press keys tool use."""
    name: Literal["computer_press_keys"]
    input: Dict[str, Any] = Field(..., description="Contains keys and press")


class TypeTextToolUseBlock(ToolUseContentBlock):
    """Type text tool use."""
    name: Literal["computer_type_text"]
    input: Dict[str, Any] = Field(..., description="Contains text, optional isSensitive and delay")


class PasteTextToolUseBlock(ToolUseContentBlock):
    """Paste text tool use."""
    name: Literal["computer_paste_text"]
    input: Dict[str, Any] = Field(..., description="Contains text and optional isSensitive")


class WaitToolUseBlock(ToolUseContentBlock):
    """Wait tool use."""
    name: Literal["computer_wait"]
    input: Dict[str, Any] = Field(..., description="Contains duration")


class ScreenshotToolUseBlock(ToolUseContentBlock):
    """Screenshot tool use."""
    name: Literal["computer_screenshot"]


class CursorPositionToolUseBlock(ToolUseContentBlock):
    """Cursor position tool use."""
    name: Literal["computer_cursor_position"]


class ApplicationToolUseBlock(ToolUseContentBlock):
    """Application tool use."""
    name: Literal["computer_application"]
    input: Dict[str, Any] = Field(..., description="Contains application")


class WriteFileToolUseBlock(ToolUseContentBlock):
    """Write file tool use."""
    name: Literal["computer_write_file"]
    input: Dict[str, Any] = Field(..., description="Contains path and data")


class ReadFileToolUseBlock(ToolUseContentBlock):
    """Read file tool use."""
    name: Literal["computer_read_file"]
    input: Dict[str, Any] = Field(..., description="Contains path")


# Union type for computer tool use blocks
ComputerToolUseContentBlock = Union[
    MoveMouseToolUseBlock,
    TraceMouseToolUseBlock,
    ClickMouseToolUseBlock,
    PressMouseToolUseBlock,
    TypeKeysToolUseBlock,
    PressKeysToolUseBlock,
    TypeTextToolUseBlock,
    PasteTextToolUseBlock,
    WaitToolUseBlock,
    ScreenshotToolUseBlock,
    DragMouseToolUseBlock,
    ScrollToolUseBlock,
    CursorPositionToolUseBlock,
    ApplicationToolUseBlock,
    WriteFileToolUseBlock,
    ReadFileToolUseBlock,
]


class UserActionContentBlock(MessageContentBlockBase):
    """User action content block."""
    type: Literal[MessageContentType.USER_ACTION]
    content: List[Union[
        ImageContentBlock,
        MoveMouseToolUseBlock,
        TraceMouseToolUseBlock,
        ClickMouseToolUseBlock,
        PressMouseToolUseBlock,
        TypeKeysToolUseBlock,
        PressKeysToolUseBlock,
        TypeTextToolUseBlock,
        DragMouseToolUseBlock,
        ScrollToolUseBlock,
    ]]


class SetTaskStatusToolUseBlock(ToolUseContentBlock):
    """Set task status tool use."""
    name: Literal["set_task_status"]
    input: Dict[str, Any] = Field(..., description="Contains status and description")


class CreateTaskToolUseBlock(ToolUseContentBlock):
    """Create task tool use."""
    name: Literal["create_task"]
    input: Dict[str, Any] = Field(..., description="Contains task creation parameters")


class ToolResultContentBlock(MessageContentBlockBase):
    """Tool result content block."""
    type: Literal[MessageContentType.TOOL_RESULT]
    tool_use_id: str
    content: List['MessageContentBlock']
    is_error: Optional[bool] = None


# Union type of all possible content blocks
MessageContentBlock = Union[
    TextContentBlock,
    ImageContentBlock,
    DocumentContentBlock,
    ToolUseContentBlock,
    ThinkingContentBlock,
    RedactedThinkingContentBlock,
    UserActionContentBlock,
    ComputerToolUseContentBlock,
    ToolResultContentBlock,
]


# Helper functions for type checking
def is_computer_tool_use_content_block(block: MessageContentBlock) -> bool:
    """Check if block is a computer tool use content block."""
    return isinstance(block, ToolUseContentBlock) and block.name.startswith("computer_")


def is_set_task_status_tool_use_block(block: MessageContentBlock) -> bool:
    """Check if block is a set task status tool use block."""
    return isinstance(block, ToolUseContentBlock) and block.name == "set_task_status"


def is_create_task_tool_use_block(block: MessageContentBlock) -> bool:
    """Check if block is a create task tool use block."""
    return isinstance(block, ToolUseContentBlock) and block.name == "create_task"