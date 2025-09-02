"""AI agent types and interfaces."""

from abc import ABC, abstractmethod
from typing import List, Literal, Optional, Protocol
from pydantic import BaseModel, Field

from shared.models.message import Message
from shared.types.message_content import MessageContentBlock


class TokenUsage(BaseModel):
    """Token usage information."""
    input_tokens: int = Field(..., description="Number of input tokens")
    output_tokens: int = Field(..., description="Number of output tokens")
    total_tokens: int = Field(..., description="Total tokens used")


class AgentResponse(BaseModel):
    """Response from AI agent."""
    content_blocks: List[MessageContentBlock] = Field(..., description="Response content blocks")
    token_usage: TokenUsage = Field(..., description="Token usage information")


class AgentModel(BaseModel):
    """AI model configuration."""
    provider: Literal["anthropic", "openai", "google", "proxy"] = Field(..., description="AI provider")
    name: str = Field(..., description="Model name")
    title: str = Field(..., description="Human-readable model title") 
    context_window: Optional[int] = Field(None, description="Context window size")


class AgentInterrupt(Exception):
    """Exception raised when agent processing is interrupted."""
    
    def __init__(self, message: str = "Agent processing interrupted"):
        super().__init__(message)
        self.name = "AgentInterrupt"


class AgentService(ABC):
    """Abstract base class for AI agent services."""
    
    @abstractmethod
    async def generate_message(
        self,
        system_prompt: str,
        messages: List[Message],
        model: str,
        use_tools: bool = True,
        signal: Optional[object] = None,  # AbortSignal equivalent
    ) -> AgentResponse:
        """Generate a message using the AI model.
        
        Args:
            system_prompt: System prompt for the conversation
            messages: List of previous messages
            model: Model name to use
            use_tools: Whether to use tools (computer actions)
            signal: Signal for cancelling the request
            
        Returns:
            AgentResponse with content blocks and token usage
        """
        pass