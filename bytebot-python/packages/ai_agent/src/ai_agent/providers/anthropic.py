"""Anthropic AI provider integration."""

import os
from typing import List, Optional

import anthropic
from anthropic.types import Message as AnthropicMessage

from shared.models.message import Message
from shared.types.message_content import MessageContentType, TextContentBlock
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
            # Make API call
            response = await self.client.messages.create(
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
            # TODO: Add support for tool use blocks
        
        return content_blocks

    def _get_computer_tools(self) -> List[dict]:
        """Get computer use tools definition for Anthropic."""
        # Simplified computer tools - would need full tool definitions
        return [
            {
                "name": "computer_screenshot",
                "description": "Take a screenshot of the current desktop",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "computer_click_mouse",
                "description": "Click the mouse at specific coordinates",
                "input_schema": {
                    "type": "object", 
                    "properties": {
                        "coordinates": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer"},
                                "y": {"type": "integer"}
                            }
                        },
                        "button": {"type": "string", "enum": ["left", "right", "middle"]},
                        "clickCount": {"type": "integer", "default": 1}
                    }
                }
            },
            {
                "name": "computer_type_text", 
                "description": "Type text on the keyboard",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"}
                    },
                    "required": ["text"]
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