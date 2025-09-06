"""Computer action utility functions for converting actions to tool use blocks."""

from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ..types.computer_action import (
    Button,
    ClickMouseAction,
    ComputerAction,
    Coordinates,
    CursorPositionAction,
    DragMouseAction,
    MoveMouseAction,
    PasteTextAction,
    Press,
    PressKeysAction,
    PressMouseAction,
    ReadFileAction,
    ScreenshotAction,
    ScrollAction,
    TraceMouseAction,
    TypeKeysAction,
    TypeTextAction,
    WaitAction,
    WriteFileAction,
)
from ..types.message_content import (
    ClickMouseToolUseBlock,
    ComputerToolUseContentBlock,
    CursorPositionToolUseBlock,
    DragMouseToolUseBlock,
    MessageContentType,
    MoveMouseToolUseBlock,
    PasteTextToolUseBlock,
    PressKeysToolUseBlock,
    PressMouseToolUseBlock,
    ReadFileToolUseBlock,
    ScreenshotToolUseBlock,
    ScrollToolUseBlock,
    TraceMouseToolUseBlock,
    TypeKeysToolUseBlock,
    TypeTextToolUseBlock,
    WaitToolUseBlock,
    WriteFileToolUseBlock,
)


def conditionally_add(obj: Dict[str, Any], conditions: List[tuple]) -> Dict[str, Any]:
    """Utility to conditionally add properties to objects."""
    result = obj.copy()
    for condition, key, value in conditions:
        if condition:
            result[key] = value
    return result


def create_tool_use_block(tool_name: str, tool_use_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Base converter for creating tool use blocks."""
    return {
        "type": MessageContentType.TOOL_USE,
        "id": tool_use_id,
        "name": tool_name,
        "input": input_data
    }


def convert_move_mouse_action_to_tool_use_block(
    action: MoveMouseAction, tool_use_id: str
) -> MoveMouseToolUseBlock:
    """Convert MoveMouseAction to tool use block."""
    return MoveMouseToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_move_mouse",
        input={"coordinates": action.coordinates.model_dump()}
    )


def convert_trace_mouse_action_to_tool_use_block(
    action: TraceMouseAction, tool_use_id: str
) -> TraceMouseToolUseBlock:
    """Convert TraceMouseAction to tool use block."""
    input_data = {"path": [coord.model_dump() for coord in action.path]}
    if action.hold_keys is not None:
        input_data["holdKeys"] = action.hold_keys
    
    return TraceMouseToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_trace_mouse",
        input=input_data
    )


def convert_click_mouse_action_to_tool_use_block(
    action: ClickMouseAction, tool_use_id: str
) -> ClickMouseToolUseBlock:
    """Convert ClickMouseAction to tool use block."""
    input_data = {
        "button": action.button.value,
        "clickCount": action.click_count
    }
    
    if action.coordinates is not None:
        input_data["coordinates"] = action.coordinates.model_dump()
    if action.hold_keys is not None:
        input_data["holdKeys"] = action.hold_keys
    
    return ClickMouseToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_click_mouse",
        input=input_data
    )


def convert_press_mouse_action_to_tool_use_block(
    action: PressMouseAction, tool_use_id: str
) -> PressMouseToolUseBlock:
    """Convert PressMouseAction to tool use block."""
    input_data = {
        "button": action.button.value,
        "press": action.press.value
    }
    
    if action.coordinates is not None:
        input_data["coordinates"] = action.coordinates.model_dump()
    
    return PressMouseToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_press_mouse",
        input=input_data
    )


def convert_drag_mouse_action_to_tool_use_block(
    action: DragMouseAction, tool_use_id: str
) -> DragMouseToolUseBlock:
    """Convert DragMouseAction to tool use block."""
    input_data = {
        "path": [coord.model_dump() for coord in action.path],
        "button": action.button.value
    }
    
    if action.hold_keys is not None:
        input_data["holdKeys"] = action.hold_keys
    
    return DragMouseToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_drag_mouse",
        input=input_data
    )


def convert_scroll_action_to_tool_use_block(
    action: ScrollAction, tool_use_id: str
) -> ScrollToolUseBlock:
    """Convert ScrollAction to tool use block."""
    input_data = {
        "direction": action.direction,
        "scrollCount": action.scroll_count
    }
    
    if action.coordinates is not None:
        input_data["coordinates"] = action.coordinates.model_dump()
    if action.hold_keys is not None:
        input_data["holdKeys"] = action.hold_keys
    
    return ScrollToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_scroll",
        input=input_data
    )


def convert_type_keys_action_to_tool_use_block(
    action: TypeKeysAction, tool_use_id: str
) -> TypeKeysToolUseBlock:
    """Convert TypeKeysAction to tool use block."""
    input_data = {"keys": action.keys}
    
    if action.delay is not None:
        input_data["delay"] = action.delay
    
    return TypeKeysToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_type_keys",
        input=input_data
    )


def convert_press_keys_action_to_tool_use_block(
    action: PressKeysAction, tool_use_id: str
) -> PressKeysToolUseBlock:
    """Convert PressKeysAction to tool use block."""
    return PressKeysToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_press_keys",
        input={
            "keys": action.keys,
            "press": action.press.value
        }
    )


def convert_type_text_action_to_tool_use_block(
    action: TypeTextAction, tool_use_id: str
) -> TypeTextToolUseBlock:
    """Convert TypeTextAction to tool use block."""
    input_data = {"text": action.text}
    
    if action.delay is not None:
        input_data["delay"] = action.delay
    if action.sensitive is not None:
        input_data["isSensitive"] = action.sensitive
    
    return TypeTextToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_type_text",
        input=input_data
    )


def convert_paste_text_action_to_tool_use_block(
    action: PasteTextAction, tool_use_id: str
) -> PasteTextToolUseBlock:
    """Convert PasteTextAction to tool use block."""
    return PasteTextToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_paste_text",
        input={"text": action.text}
    )


def convert_wait_action_to_tool_use_block(
    action: WaitAction, tool_use_id: str
) -> WaitToolUseBlock:
    """Convert WaitAction to tool use block."""
    return WaitToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_wait",
        input={"duration": action.duration}
    )


def convert_screenshot_action_to_tool_use_block(
    action: ScreenshotAction, tool_use_id: str
) -> ScreenshotToolUseBlock:
    """Convert ScreenshotAction to tool use block."""
    return ScreenshotToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_screenshot",
        input={}
    )


def convert_cursor_position_action_to_tool_use_block(
    action: CursorPositionAction, tool_use_id: str
) -> CursorPositionToolUseBlock:
    """Convert CursorPositionAction to tool use block."""
    return CursorPositionToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_cursor_position",
        input={}
    )


def convert_write_file_action_to_tool_use_block(
    action: WriteFileAction, tool_use_id: str
) -> WriteFileToolUseBlock:
    """Convert WriteFileAction to tool use block."""
    return WriteFileToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_write_file",
        input={
            "path": action.path,
            "data": action.data
        }
    )


def convert_read_file_action_to_tool_use_block(
    action: ReadFileAction, tool_use_id: str
) -> ReadFileToolUseBlock:
    """Convert ReadFileAction to tool use block."""
    return ReadFileToolUseBlock(
        type=MessageContentType.TOOL_USE,
        id=tool_use_id,
        name="computer_read_file",
        input={"path": action.path}
    )


def convert_computer_action_to_tool_use_block(
    action: ComputerAction, tool_use_id: str
) -> ComputerToolUseContentBlock:
    """Generic converter that handles all action types."""
    if action.action == "move_mouse":
        return convert_move_mouse_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "trace_mouse":
        return convert_trace_mouse_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "click_mouse":
        return convert_click_mouse_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "press_mouse":
        return convert_press_mouse_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "drag_mouse":
        return convert_drag_mouse_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "scroll":
        return convert_scroll_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "type_keys":
        return convert_type_keys_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "press_keys":
        return convert_press_keys_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "type_text":
        return convert_type_text_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "paste_text":
        return convert_paste_text_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "wait":
        return convert_wait_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "screenshot":
        return convert_screenshot_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "cursor_position":
        return convert_cursor_position_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "write_file":
        return convert_write_file_action_to_tool_use_block(action, tool_use_id)
    elif action.action == "read_file":
        return convert_read_file_action_to_tool_use_block(action, tool_use_id)
    else:
        raise ValueError(f"Unknown action type: {action.action}")


# Type guards for computer actions
def is_move_mouse_action(obj: Any) -> bool:
    """Check if object is a MoveMouseAction."""
    return hasattr(obj, 'action') and obj.action == "move_mouse"


def is_trace_mouse_action(obj: Any) -> bool:
    """Check if object is a TraceMouseAction."""
    return hasattr(obj, 'action') and obj.action == "trace_mouse"


def is_click_mouse_action(obj: Any) -> bool:
    """Check if object is a ClickMouseAction."""
    return hasattr(obj, 'action') and obj.action == "click_mouse"


def is_press_mouse_action(obj: Any) -> bool:
    """Check if object is a PressMouseAction."""
    return hasattr(obj, 'action') and obj.action == "press_mouse"


def is_drag_mouse_action(obj: Any) -> bool:
    """Check if object is a DragMouseAction."""
    return hasattr(obj, 'action') and obj.action == "drag_mouse"


def is_scroll_action(obj: Any) -> bool:
    """Check if object is a ScrollAction."""
    return hasattr(obj, 'action') and obj.action == "scroll"


def is_type_keys_action(obj: Any) -> bool:
    """Check if object is a TypeKeysAction."""
    return hasattr(obj, 'action') and obj.action == "type_keys"


def is_press_keys_action(obj: Any) -> bool:
    """Check if object is a PressKeysAction."""
    return hasattr(obj, 'action') and obj.action == "press_keys"


def is_type_text_action(obj: Any) -> bool:
    """Check if object is a TypeTextAction."""
    return hasattr(obj, 'action') and obj.action == "type_text"


def is_paste_text_action(obj: Any) -> bool:
    """Check if object is a PasteTextAction."""
    return hasattr(obj, 'action') and obj.action == "paste_text"


def is_wait_action(obj: Any) -> bool:
    """Check if object is a WaitAction."""
    return hasattr(obj, 'action') and obj.action == "wait"


def is_screenshot_action(obj: Any) -> bool:
    """Check if object is a ScreenshotAction."""
    return hasattr(obj, 'action') and obj.action == "screenshot"


def is_cursor_position_action(obj: Any) -> bool:
    """Check if object is a CursorPositionAction."""
    return hasattr(obj, 'action') and obj.action == "cursor_position"


def is_write_file_action(obj: Any) -> bool:
    """Check if object is a WriteFileAction."""
    return hasattr(obj, 'action') and obj.action == "write_file"


def is_read_file_action(obj: Any) -> bool:
    """Check if object is a ReadFileAction."""
    return hasattr(obj, 'action') and obj.action == "read_file"