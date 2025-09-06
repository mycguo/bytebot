"""Input capture service for recording user actions during Take Over mode."""

import logging
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from shared.types.message_content import (
    MessageContentType,
    UserActionContentBlock,
    ImageContentBlock,
    ImageSource,
)
from shared.utils.computer_action_utils import (
    convert_click_mouse_action_to_tool_use_block,
    convert_drag_mouse_action_to_tool_use_block,
    convert_type_text_action_to_tool_use_block,
    convert_type_keys_action_to_tool_use_block,
    convert_scroll_action_to_tool_use_block,
    convert_press_mouse_action_to_tool_use_block,
    convert_press_keys_action_to_tool_use_block,
)
from shared.types.computer_action import (
    ClickMouseAction,
    DragMouseAction,
    TypeTextAction,
    TypeKeysAction,
    ScrollAction,
    PressMouseAction,
    PressKeysAction,
    Button,
    Coordinates,
    Press,
)

logger = logging.getLogger(__name__)


class InputCaptureService:
    """Service for capturing user input and converting to message format."""
    
    def __init__(self):
        self.capturing = False
        self.current_task_id: Optional[str] = None
        self.captured_actions: List[Dict[str, Any]] = []
        
    def is_capturing(self) -> bool:
        """Check if input capture is currently active."""
        return self.capturing
    
    def start_capture(self, task_id: str) -> bool:
        """Start capturing input for the given task."""
        try:
            if self.capturing:
                logger.warning(f"Input capture already active for task {self.current_task_id}")
                return False
            
            self.capturing = True
            self.current_task_id = task_id
            self.captured_actions = []
            
            logger.info(f"Started input capture for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start input capture: {e}")
            return False
    
    def stop_capture(self) -> bool:
        """Stop input capture."""
        try:
            if not self.capturing:
                logger.warning("Input capture not active")
                return False
            
            self.capturing = False
            task_id = self.current_task_id
            self.current_task_id = None
            
            logger.info(f"Stopped input capture for task {task_id}. Captured {len(self.captured_actions)} actions.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop input capture: {e}")
            return False
    
    def capture_click_action(self, x: int, y: int, button: str = "left", click_count: int = 1, 
                           hold_keys: Optional[List[str]] = None, screenshot_data: Optional[str] = None) -> bool:
        """Capture a mouse click action."""
        if not self.capturing or not self.current_task_id:
            return False
        
        try:
            # Create click action
            action = ClickMouseAction(
                action="click_mouse",
                coordinates=Coordinates(x=x, y=y),
                button=Button(button),
                click_count=click_count,
                hold_keys=hold_keys
            )
            
            # Convert to tool use block
            tool_use_id = str(uuid.uuid4())
            tool_use_block = convert_click_mouse_action_to_tool_use_block(action, tool_use_id)
            
            # Create user action content block
            user_action = self._create_user_action_block([tool_use_block], screenshot_data)
            
            # Store the action
            self.captured_actions.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action_type": "click_mouse",
                "user_action": user_action.model_dump(),
                "task_id": self.current_task_id
            })
            
            logger.info(f"Captured click action at ({x}, {y}) with {button} button")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture click action: {e}")
            return False
    
    def capture_drag_action(self, path: List[Dict[str, int]], button: str = "left", 
                          hold_keys: Optional[List[str]] = None, screenshot_data: Optional[str] = None) -> bool:
        """Capture a mouse drag action."""
        if not self.capturing or not self.current_task_id:
            return False
        
        try:
            # Convert path coordinates
            coordinates_path = [Coordinates(x=coord["x"], y=coord["y"]) for coord in path]
            
            # Create drag action
            action = DragMouseAction(
                action="drag_mouse",
                path=coordinates_path,
                button=Button(button),
                hold_keys=hold_keys
            )
            
            # Convert to tool use block
            tool_use_id = str(uuid.uuid4())
            tool_use_block = convert_drag_mouse_action_to_tool_use_block(action, tool_use_id)
            
            # Create user action content block
            user_action = self._create_user_action_block([tool_use_block], screenshot_data)
            
            # Store the action
            self.captured_actions.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action_type": "drag_mouse",
                "user_action": user_action.model_dump(),
                "task_id": self.current_task_id
            })
            
            logger.info(f"Captured drag action with {len(path)} points")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture drag action: {e}")
            return False
    
    def capture_type_text_action(self, text: str, delay: Optional[int] = None, 
                               sensitive: bool = False, screenshot_data: Optional[str] = None) -> bool:
        """Capture a type text action."""
        if not self.capturing or not self.current_task_id:
            return False
        
        try:
            # Create type text action
            action = TypeTextAction(
                action="type_text",
                text=text,
                delay=delay,
                sensitive=sensitive
            )
            
            # Convert to tool use block
            tool_use_id = str(uuid.uuid4())
            tool_use_block = convert_type_text_action_to_tool_use_block(action, tool_use_id)
            
            # Create user action content block
            user_action = self._create_user_action_block([tool_use_block], screenshot_data)
            
            # Store the action
            self.captured_actions.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action_type": "type_text",
                "user_action": user_action.model_dump(),
                "task_id": self.current_task_id
            })
            
            logger.info(f"Captured type text action: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture type text action: {e}")
            return False
    
    def capture_scroll_action(self, x: int, y: int, direction: str, scroll_count: int = 3,
                            hold_keys: Optional[List[str]] = None, screenshot_data: Optional[str] = None) -> bool:
        """Capture a scroll action."""
        if not self.capturing or not self.current_task_id:
            return False
        
        try:
            # Create scroll action
            action = ScrollAction(
                action="scroll",
                coordinates=Coordinates(x=x, y=y),
                direction=direction,
                scroll_count=scroll_count,
                hold_keys=hold_keys
            )
            
            # Convert to tool use block
            tool_use_id = str(uuid.uuid4())
            tool_use_block = convert_scroll_action_to_tool_use_block(action, tool_use_id)
            
            # Create user action content block
            user_action = self._create_user_action_block([tool_use_block], screenshot_data)
            
            # Store the action
            self.captured_actions.append({
                "timestamp": datetime.utcnow().isoformat(),
                "action_type": "scroll",
                "user_action": user_action.model_dump(),
                "task_id": self.current_task_id
            })
            
            logger.info(f"Captured scroll action at ({x}, {y}) direction {direction}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to capture scroll action: {e}")
            return False
    
    def _create_user_action_block(self, tool_use_blocks: List[Any], 
                                screenshot_data: Optional[str] = None) -> UserActionContentBlock:
        """Create a user action content block with optional screenshot."""
        content = []
        
        # Add screenshot if provided
        if screenshot_data:
            image_block = ImageContentBlock(
                type=MessageContentType.IMAGE,
                source=ImageSource(
                    data=screenshot_data,
                    media_type="image/png",
                    type="base64"
                )
            )
            content.append(image_block)
        
        # Add tool use blocks
        content.extend(tool_use_blocks)
        
        return UserActionContentBlock(
            type=MessageContentType.USER_ACTION,
            content=content
        )
    
    def get_captured_actions(self) -> List[Dict[str, Any]]:
        """Get all captured actions for the current session."""
        return self.captured_actions.copy()
    
    def clear_captured_actions(self) -> None:
        """Clear all captured actions."""
        self.captured_actions = []
        logger.info("Cleared captured actions")
    
    async def send_captured_actions_to_task(self, api_client) -> bool:
        """Send all captured actions to the current task as user messages."""
        if not self.current_task_id or not self.captured_actions:
            return False
        
        try:
            for action in self.captured_actions:
                user_action = action["user_action"]
                
                # This would call an API endpoint to add the user action to the task's message history
                # For now, we'll just log it
                logger.info(f"Would send user action to task {self.current_task_id}: {action['action_type']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send captured actions: {e}")
            return False


# Global input capture service instance
input_capture_service = InputCaptureService()