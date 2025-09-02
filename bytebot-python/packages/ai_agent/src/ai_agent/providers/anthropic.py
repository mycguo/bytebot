"""Anthropic AI provider integration."""

import os
from typing import List, Optional

import anthropic
from anthropic.types import Message as AnthropicMessage

from shared.models.message import Message
from shared.types.message_content import MessageContentType, TextContentBlock, ToolUseContentBlock
from ..models.agent_types import AgentResponse, TokenUsage
from .base import BaseAIProvider


class AnthropicService(BaseAIProvider):
    """Anthropic Claude AI service."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")
        
        self.client = anthropic.Anthropic(api_key=api_key)

    async def generate_message(
        self,
        system_prompt: str,
        messages: List[Message],
        model: str,
        use_tools: bool = True,
        signal: Optional[object] = None,
    ) -> AgentResponse:
        """Generate message using Anthropic Claude."""
        
        # Convert messages to Anthropic format
        anthropic_messages = self._convert_messages(messages)
        
        # Define tools if needed
        tools = self._get_computer_tools() if use_tools else None
        
        try:
            # Make API call (synchronous - Anthropic client doesn't support async)
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=anthropic_messages,
                tools=tools,
            )
            
            # Convert response back to our format
            content_blocks = self._convert_response_content(response.content)
            
            token_usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            )
            
            return AgentResponse(
                content_blocks=content_blocks,
                token_usage=token_usage
            )
            
        except Exception as e:
            # Return error as text response
            return AgentResponse(
                content_blocks=[
                    TextContentBlock(
                        type=MessageContentType.TEXT,
                        text=f"Error from Anthropic API: {str(e)}"
                    )
                ],
                token_usage=TokenUsage(
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0
                )
            )

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert our message format to Anthropic format."""
        anthropic_messages = []
        
        for msg in messages:
            # Convert role
            role = "user" if msg.role.value == "USER" else "assistant"
            
            # Convert content - for now, simple text extraction
            content_text = ""
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        content_text += block.get("text", "")
            
            if content_text:
                anthropic_messages.append({
                    "role": role,
                    "content": content_text
                })
        
        return anthropic_messages

    def _convert_response_content(self, content) -> List:
        """Convert Anthropic response content to our format."""
        content_blocks = []
        
        for block in content:
            if block.type == "text":
                content_blocks.append(
                    TextContentBlock(
                        type=MessageContentType.TEXT,
                        text=block.text
                    )
                )
            elif block.type == "tool_use":
                content_blocks.append(
                    ToolUseContentBlock(
                        type=MessageContentType.TOOL_USE,
                        id=block.id,
                        name=block.name,
                        input=block.input
                    )
                )
        
        return content_blocks

    def _get_computer_tools(self) -> List[dict]:
        """Get comprehensive computer use tools definition for Anthropic."""
        return [
            {
                "name": "computer_screenshot",
                "description": "Take a screenshot of the current desktop to see what's displayed",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "computer_click_mouse",
                "description": "Click the mouse at specific coordinates on the screen",
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "coordinates": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer", "description": "X coordinate in pixels"},
                                "y": {"type": "integer", "description": "Y coordinate in pixels"}
                            },
                            "required": ["x", "y"]
                        },
                        "button": {
                            "type": "string", 
                            "enum": ["left", "right", "middle"], 
                            "default": "left",
                            "description": "Mouse button to click"
                        },
                        "clickCount": {
                            "type": "integer", 
                            "default": 1,
                            "description": "Number of clicks (1=single, 2=double, etc.)"
                        },
                        "holdKeys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keys to hold while clicking (e.g., ['ctrl', 'shift'])"
                        }
                    },
                    "required": ["coordinates"]
                }
            },
            {
                "name": "computer_move_mouse",
                "description": "Move the mouse to specific coordinates without clicking",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "coordinates": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer", "description": "X coordinate in pixels"},
                                "y": {"type": "integer", "description": "Y coordinate in pixels"}
                            },
                            "required": ["x", "y"]
                        }
                    },
                    "required": ["coordinates"]
                }
            },
            {
                "name": "computer_press_mouse",
                "description": "Press or release mouse button at current position or specific coordinates",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "coordinates": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer"},
                                "y": {"type": "integer"}
                            },
                            "description": "Optional coordinates to move to before pressing"
                        },
                        "button": {
                            "type": "string", 
                            "enum": ["left", "right", "middle"], 
                            "default": "left"
                        },
                        "press": {
                            "type": "string",
                            "enum": ["down", "up"],
                            "description": "Press down or release the button"
                        }
                    },
                    "required": ["press"]
                }
            },
            {
                "name": "computer_drag_mouse",
                "description": "Drag the mouse from one location to another while holding a button",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"}
                                },
                                "required": ["x", "y"]
                            },
                            "description": "Path of coordinates to drag along"
                        },
                        "button": {
                            "type": "string", 
                            "enum": ["left", "right", "middle"], 
                            "default": "left"
                        },
                        "holdKeys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keys to hold during drag"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "computer_trace_mouse",
                "description": "Move the mouse along a path without clicking (for hovering)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"}
                                },
                                "required": ["x", "y"]
                            },
                            "description": "Path of coordinates to trace"
                        },
                        "holdKeys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keys to hold while tracing"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "computer_scroll",
                "description": "Scroll at specific coordinates or current mouse position",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "coordinates": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer"},
                                "y": {"type": "integer"}
                            },
                            "description": "Optional coordinates to scroll at"
                        },
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down", "left", "right"],
                            "description": "Direction to scroll"
                        },
                        "scrollCount": {
                            "type": "integer",
                            "default": 3,
                            "description": "Number of scroll steps"
                        },
                        "holdKeys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keys to hold while scrolling"
                        }
                    },
                    "required": ["direction"]
                }
            },
            {
                "name": "computer_type_text", 
                "description": "Type natural text on the keyboard (for regular text input)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to type"
                        },
                        "delay": {
                            "type": "integer",
                            "description": "Delay between characters in milliseconds"
                        },
                        "sensitive": {
                            "type": "boolean",
                            "default": False,
                            "description": "Mark as sensitive to avoid logging"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "computer_paste_text",
                "description": "Paste text using clipboard (faster for large text)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to paste"
                        }
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "computer_type_keys",
                "description": "Type specific key sequences (for shortcuts, special keys, etc.)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of keys to type in sequence"
                        },
                        "delay": {
                            "type": "integer",
                            "description": "Delay between keys in milliseconds"
                        }
                    },
                    "required": ["keys"]
                }
            },
            {
                "name": "computer_press_keys",
                "description": "Press or release specific keys (for key combinations, modifiers)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of keys to press/release"
                        },
                        "press": {
                            "type": "string", 
                            "enum": ["down", "up"], 
                            "default": "down",
                            "description": "Press down or release keys"
                        }
                    },
                    "required": ["keys"]
                }
            },
            {
                "name": "computer_application",
                "description": "Launch or switch to applications",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "application": {
                            "type": "string", 
                            "enum": ["firefox", "vscode", "terminal", "desktop"],
                            "description": "Application to launch or switch to"
                        }
                    },
                    "required": ["application"]
                }
            },
            {
                "name": "computer_wait",
                "description": "Wait for a specified duration (useful for letting UI load)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "duration": {
                            "type": "integer",
                            "description": "Duration to wait in milliseconds"
                        }
                    },
                    "required": ["duration"]
                }
            },
            {
                "name": "computer_cursor_position",
                "description": "Get current cursor/mouse position coordinates",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "computer_write_file",
                "description": "Write binary data to a file (e.g., save downloaded files)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to write to"
                        },
                        "data": {
                            "type": "string",
                            "description": "Base64 encoded data to write"
                        }
                    },
                    "required": ["path", "data"]
                }
            },
            {
                "name": "computer_read_file",
                "description": "Read a file and return as base64 data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to read from"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "set_task_status",
                "description": "Set the current task status (completed, failed, or needs help)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["completed", "failed", "needs_help"],
                            "description": "Task completion status"
                        },
                        "description": {
                            "type": "string",
                            "description": "Description of the result or issue"
                        }
                    },
                    "required": ["status"]
                }
            }
        ]

    def get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022", 
            "claude-3-opus-20240229"
        ]

    def supports_tools(self) -> bool:
        """Anthropic supports tool calling."""
        return True