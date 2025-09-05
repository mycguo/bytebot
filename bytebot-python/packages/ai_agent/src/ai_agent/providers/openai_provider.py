"""OpenAI provider integration."""

import os
from typing import List, Optional
import json

from openai import OpenAI
from shared.models.message import Message
from shared.types.message_content import MessageContentType, TextContentBlock, ToolUseContentBlock
from ..models.agent_types import AgentResponse, TokenUsage
from .base import BaseAIProvider


class OpenAIService(BaseAIProvider):
    """OpenAI GPT service."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = OpenAI(api_key=api_key)

    async def generate_message(
        self,
        system_prompt: str,
        messages: List[Message],
        model: str,
        use_tools: bool = True,
        signal: Optional[object] = None,
    ) -> AgentResponse:
        """Generate message using OpenAI GPT."""
        
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages, system_prompt)
        
        # Define tools if needed
        tools = self._get_computer_tools() if use_tools else None
        
        try:
            # Make API call
            kwargs = {
                "model": model,
                "max_tokens": 4096,
                "messages": openai_messages,
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**kwargs)
            
            # Convert response back to our format
            content_blocks = self._convert_response_content(response.choices[0].message)
            
            token_usage = TokenUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
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
                        text=f"Error from OpenAI API: {str(e)}"
                    )
                ],
                token_usage=TokenUsage(
                    input_tokens=0,
                    output_tokens=0,
                    total_tokens=0
                )
            )

    def _convert_messages(self, messages: List[Message], system_prompt: str) -> List[dict]:
        """Convert our message format to OpenAI format."""
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        for msg in messages:
            # Convert role
            role = "user" if msg.role.value == "USER" else "assistant"
            
            # Convert content - handle both text and images
            content_parts = []
            has_content = False
            
            if isinstance(msg.content, list):
                for block in msg.content:
                    if isinstance(block, dict):
                        if block.get("type") == "text" and block.get("text"):
                            content_parts.append({
                                "type": "text",
                                "text": block.get("text")
                            })
                            has_content = True
                        elif block.get("type") == "image" and block.get("source"):
                            # Handle base64 images for vision
                            source = block.get("source", {})
                            if source.get("type") == "base64" and source.get("data"):
                                media_type = source.get("media_type", "image/png")
                                content_parts.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{media_type};base64,{source.get('data')}"
                                    }
                                })
                                has_content = True
            
            # If we have content parts (text + images), use the multi-part format
            # If only text, use simple string format for compatibility
            if has_content:
                if len(content_parts) == 1 and content_parts[0]["type"] == "text":
                    # Simple text-only message
                    openai_messages.append({
                        "role": role,
                        "content": content_parts[0]["text"]
                    })
                else:
                    # Multi-part message with images
                    openai_messages.append({
                        "role": role,
                        "content": content_parts
                    })
        
        return openai_messages

    def _convert_response_content(self, message) -> List:
        """Convert OpenAI response content to our format."""
        content_blocks = []
        
        # Handle text content
        if message.content:
            content_blocks.append(
                TextContentBlock(
                    type=MessageContentType.TEXT,
                    text=message.content
                )
            )
        
        # Handle tool calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                content_blocks.append(
                    ToolUseContentBlock(
                        type=MessageContentType.TOOL_USE,
                        id=tool_call.id,
                        name=tool_call.function.name,
                        input=json.loads(tool_call.function.arguments)
                    )
                )
        
        return content_blocks

    def _get_computer_tools(self) -> List[dict]:
        """Get comprehensive computer use tools definition for OpenAI."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "computer_screenshot",
                    "description": "Take a screenshot of the current desktop to see what's displayed",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "computer_application",
                    "description": "Launch or switch to applications",
                    "parameters": {
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
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "computer_click_mouse",
                    "description": "Click the mouse at specific coordinates on the screen",
                    "parameters": {
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
                                "description": "Mouse button to click"
                            },
                            "clickCount": {
                                "type": "integer",
                                "description": "Number of clicks (1=single, 2=double, etc.)"
                            }
                        },
                        "required": ["coordinates"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "computer_type_text",
                    "description": "Type natural text on the keyboard (for regular text input)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to type"
                            }
                        },
                        "required": ["text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_task_status",
                    "description": "Set the current task status (completed, failed, or needs help)",
                    "parameters": {
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
            }
        ]

    def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        return [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]

    def supports_tools(self) -> bool:
        """OpenAI supports function calling."""
        return True