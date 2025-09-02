"""API client for communicating with Bytebot services."""

import httpx
import asyncio
import streamlit as st
from typing import Dict, List, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)


class APIClient:
    """Client for interacting with Bytebot API services."""
    
    def __init__(
        self,
        agent_base_url: str = None,
        computer_base_url: str = None,
        timeout: float = 30.0
    ):
        # Use environment variables if URLs not provided
        if agent_base_url is None:
            agent_host = os.getenv("AI_AGENT_HOST", "localhost")
            agent_port = os.getenv("AI_AGENT_PORT", "9996")
            agent_base_url = f"http://{agent_host}:{agent_port}"
        
        if computer_base_url is None:
            computer_host = os.getenv("COMPUTER_CONTROL_HOST", "localhost")
            computer_port = os.getenv("COMPUTER_CONTROL_PORT", "9995")
            computer_base_url = f"http://{computer_host}:{computer_port}"
        
        self.agent_base_url = agent_base_url.rstrip("/")
        self.computer_base_url = computer_base_url.rstrip("/")
        self.timeout = timeout

    async def get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make GET request to AI agent service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.agent_base_url}{endpoint}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error making GET request to {endpoint}: {e}")
            return None

    async def post(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make POST request to AI agent service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.agent_base_url}{endpoint}", json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error making POST request to {endpoint}: {e}")
            return None

    async def get_computer(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make GET request to computer control service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.computer_base_url}{endpoint}")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error making GET request to computer service {endpoint}: {e}")
            return None

    async def post_computer(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make POST request to computer control service."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.computer_base_url}{endpoint}", json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error making POST request to computer service {endpoint}: {e}")
            return None

    # Task Management Methods
    async def create_task(self, description: str, priority: str = "MEDIUM", model: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Create a new task."""
        if model is None:
            model = {
                "provider": "anthropic",
                "name": "claude-3-5-sonnet-20241022",
                "title": "Claude 3.5 Sonnet"
            }
        
        data = {
            "description": description,
            "priority": priority,
            "type": "IMMEDIATE", 
            "model": model
        }
        
        return await self.post("/tasks", data)

    async def get_tasks(self, limit: int = 50, status: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get list of tasks."""
        endpoint = f"/tasks?limit={limit}"
        if status:
            endpoint += f"&status={status}"
        
        return await self.get(endpoint)

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task."""
        return await self.get(f"/tasks/{task_id}")

    async def process_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Manually trigger task processing."""
        return await self.post(f"/tasks/{task_id}/process", {})

    async def abort_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Abort task processing."""
        return await self.post(f"/tasks/{task_id}/abort", {})

    async def get_processor_status(self) -> Optional[Dict[str, Any]]:
        """Get processor status."""
        return await self.get("/processor/status")

    # Computer Control Methods
    async def take_screenshot(self) -> Optional[Dict[str, Any]]:
        """Take a screenshot of the desktop."""
        data = {"action": "screenshot"}
        return await self.post_computer("/computer-use", data)

    async def click_mouse(self, x: int, y: int, button: str = "left") -> Optional[Dict[str, Any]]:
        """Click mouse at coordinates."""
        data = {
            "action": "click_mouse",
            "coordinates": {"x": x, "y": y},
            "button": button,
            "clickCount": 1
        }
        return await self.post_computer("/computer-use", data)

    async def type_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Type text."""
        data = {
            "action": "type_text", 
            "text": text
        }
        return await self.post_computer("/computer-use", data)