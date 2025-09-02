"""Base AI provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from shared.models.message import Message
from ..models.agent_types import AgentResponse, AgentService


class BaseAIProvider(AgentService, ABC):
    """Base class for AI providers."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abstractmethod
    async def generate_message(
        self,
        system_prompt: str,
        messages: List[Message],
        model: str,
        use_tools: bool = True,
        signal: Optional[object] = None,
    ) -> AgentResponse:
        """Generate a message using the AI provider."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if provider supports tool calling."""
        pass