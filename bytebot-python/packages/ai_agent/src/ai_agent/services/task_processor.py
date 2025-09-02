"""Task processor for AI agent coordination."""

import asyncio
import logging
import os
from typing import Dict, Optional
from uuid import UUID

import httpx
from shared.models.task import TaskStatus, Role
from shared.database.session import get_db_session
from shared.types.message_content import (
    MessageContentBlock, 
    MessageContentType,
    TextContentBlock,
    ToolUseContentBlock,
    ToolResultContentBlock,
    is_computer_tool_use_content_block,
    is_set_task_status_tool_use_block,
)

from .task_service import TaskService
from ..models.constants import AGENT_SYSTEM_PROMPT
from ..models.agent_types import AgentInterrupt
from ..providers.anthropic import AnthropicService


class TaskProcessor:
    """Processes tasks using AI agents."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_task_id: Optional[str] = None
        self.is_processing = False
        self.abort_controllers: Dict[str, asyncio.Event] = {}
        
        # Computer control service URL - use environment variable
        self.computer_control_url = os.getenv("COMPUTER_CONTROL_URL", "http://computer-control:9995")
        
        # Initialize AI provider
        try:
            self.ai_provider = AnthropicService()
            self.logger.info("Anthropic AI provider initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize AI provider: {e}")
            self.ai_provider = None
        
        self.logger.info("TaskProcessor initialized")

    def is_running(self) -> bool:
        """Check if processor is currently running."""
        return self.is_processing

    def get_current_task_id(self) -> Optional[str]:
        """Get current task ID being processed."""
        return self.current_task_id

    async def process_task(self, task_id: str) -> None:
        """Process a single task."""
        self.logger.info(f"Starting to process task {task_id}")
        
        # Set up abort controller
        abort_event = asyncio.Event()
        self.abort_controllers[task_id] = abort_event
        
        try:
            self.current_task_id = task_id
            self.is_processing = True
            
            with get_db_session() as db:
                task_service = TaskService(db)
                
                # Get task
                task = await task_service.get_task(UUID(task_id))
                if not task:
                    self.logger.error(f"Task {task_id} not found")
                    return
                
                # Update status to running
                await task_service.update_task_status(
                    UUID(task_id), 
                    TaskStatus.RUNNING
                )
                
                # Get task messages
                messages = await task_service.get_task_messages(UUID(task_id))
                
                # If no messages, create initial user message
                if not messages:
                    await task_service.add_message(
                        task_id=UUID(task_id),
                        content=[{
                            "type": MessageContentType.TEXT.value,
                            "text": task.description
                        }],
                        role=Role.USER
                    )
                    # Refresh messages
                    messages = await task_service.get_task_messages(UUID(task_id))
                
                # Process task with AI
                try:
                    await self._process_with_ai(task_service, task, messages, abort_event)
                    
                    # Mark as completed if not already set
                    current_task = await task_service.get_task(UUID(task_id))
                    if current_task and current_task.status == TaskStatus.RUNNING:
                        await task_service.update_task_status(
                            UUID(task_id),
                            TaskStatus.COMPLETED
                        )
                        
                except AgentInterrupt:
                    self.logger.info(f"Task {task_id} processing was interrupted")
                    await task_service.update_task_status(
                        UUID(task_id),
                        TaskStatus.CANCELLED,
                        error="Processing was interrupted"
                    )
                except Exception as e:
                    self.logger.error(f"Error processing task {task_id}: {e}", exc_info=True)
                    await task_service.update_task_status(
                        UUID(task_id),
                        TaskStatus.FAILED,
                        error=str(e)
                    )
                
        finally:
            # Clean up
            self.current_task_id = None
            self.is_processing = False
            self.abort_controllers.pop(task_id, None)
            
        self.logger.info(f"Finished processing task {task_id}")

    async def abort_task(self, task_id: str) -> None:
        """Abort task processing."""
        self.logger.info(f"Aborting task {task_id}")
        
        if task_id in self.abort_controllers:
            self.abort_controllers[task_id].set()
        
        # Update task status
        with get_db_session() as db:
            task_service = TaskService(db)
            await task_service.update_task_status(
                UUID(task_id),
                TaskStatus.CANCELLED,
                error="Task aborted by user"
            )

    async def _process_with_ai(self, task_service: TaskService, task, messages, abort_event: asyncio.Event):
        """Process task using AI agent."""
        if not self.ai_provider:
            # Fallback to placeholder response if AI provider not available
            self.logger.warning("AI provider not available, using placeholder response")
            response_content = [
                TextContentBlock(
                    type=MessageContentType.TEXT,
                    text=f"AI provider not available. Task: {task.description}"
                )
            ]
            
            await task_service.add_message(
                task_id=task.id,
                content=[block.model_dump() for block in response_content],
                role=Role.ASSISTANT
            )
            return
        
        max_iterations = 20  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            if abort_event.is_set():
                raise AgentInterrupt("Task processing was aborted")
            
            iteration += 1
            self.logger.debug(f"Task {task.id} - Iteration {iteration}")
            
            # Get model configuration from task
            model_config = task.model if hasattr(task, 'model') and task.model else {
                "name": "claude-3-5-sonnet-20241022"
            }
            
            try:
                # Call real AI provider
                response = await self.ai_provider.generate_message(
                    system_prompt=AGENT_SYSTEM_PROMPT,
                    messages=messages,
                    model=model_config.get("name", "claude-3-5-sonnet-20241022"),
                    use_tools=True,
                    signal=abort_event
                )
                
                # Add AI response message
                await task_service.add_message(
                    task_id=task.id,
                    content=[block.model_dump() for block in response.content_blocks],
                    role=Role.ASSISTANT
                )
                
                # Check for tool use in response
                tool_results = []
                has_computer_tools = False
                task_completed = False
                
                for block in response.content_blocks:
                    if isinstance(block, ToolUseContentBlock):
                        if is_computer_tool_use_content_block(block):
                            has_computer_tools = True
                            # Execute computer tool
                            result = await self._execute_computer_tool(block)
                            tool_results.append(result)
                        elif is_set_task_status_tool_use_block(block):
                            # Handle task status change
                            await self._handle_task_status_change(task_service, task.id, block)
                            task_completed = True
                            return  # Task is complete
                
                # If task was completed via tool, exit
                if task_completed:
                    return
                    
                # Add tool results if any
                if tool_results:
                    for result in tool_results:
                        await task_service.add_message(
                            task_id=task.id,
                            content=[result.model_dump()],
                            role=Role.ASSISTANT
                        )
                    
                    # Refresh messages for next iteration
                    messages = await task_service.get_task_messages(task.id)
                else:
                    # If no tools used and it's a text response, consider task complete
                    self.logger.info(f"Task {task.id} completed with text response")
                    break
                
                # Small delay between iterations
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in AI processing for task {task.id}: {e}")
                # Add error message
                error_response = [
                    TextContentBlock(
                        type=MessageContentType.TEXT,
                        text=f"Error processing task: {str(e)}"
                    )
                ]
                await task_service.add_message(
                    task_id=task.id,
                    content=[block.model_dump() for block in error_response],
                    role=Role.ASSISTANT
                )
                break
        
        if iteration >= max_iterations:
            self.logger.warning(f"Task {task.id} reached maximum iterations ({max_iterations})")

    async def _execute_computer_tool(self, tool_block: ToolUseContentBlock) -> ToolResultContentBlock:
        """Execute a computer tool use block."""
        self.logger.info(f"Executing computer tool: {tool_block.name}")
        
        try:
            # Prepare the computer action
            computer_action = {
                "action": tool_block.name.replace("computer_", ""),
                **tool_block.input
            }
            
            # Send to computer control service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.computer_control_url}/computer-use",
                    json=computer_action,
                    timeout=30.0
                )
                response.raise_for_status()
                result_data = response.json()
            
            # Create tool result
            result_content = [
                TextContentBlock(
                    type=MessageContentType.TEXT,
                    text=f"Computer action '{tool_block.name}' completed successfully."
                )
            ]
            
            # Add image data for screenshots
            if "data" in result_data and "type" in result_data:
                if result_data["type"] == "image":
                    from shared.types.message_content import ImageContentBlock, ImageSource
                    image_block = ImageContentBlock(
                        type=MessageContentType.IMAGE,
                        source=ImageSource(
                            media_type="image/png",
                            type="base64",
                            data=result_data["data"]
                        )
                    )
                    result_content.append(image_block)
            
            return ToolResultContentBlock(
                type=MessageContentType.TOOL_RESULT,
                tool_use_id=tool_block.id,
                content=result_content
            )
            
        except Exception as e:
            self.logger.error(f"Error executing computer tool {tool_block.name}: {e}")
            
            return ToolResultContentBlock(
                type=MessageContentType.TOOL_RESULT,
                tool_use_id=tool_block.id,
                content=[
                    TextContentBlock(
                        type=MessageContentType.TEXT,
                        text=f"Error executing {tool_block.name}: {str(e)}"
                    )
                ],
                is_error=True
            )

    async def _handle_task_status_change(self, task_service: TaskService, task_id: UUID, tool_block: ToolUseContentBlock):
        """Handle task status change tool."""
        status_input = tool_block.input
        status = status_input.get("status")
        description = status_input.get("description", "")
        
        if status == "completed":
            await task_service.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                result={"description": description}
            )
        elif status == "failed":
            await task_service.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=description
            )
        elif status == "needs_help":
            await task_service.update_task_status(
                task_id,
                TaskStatus.NEEDS_HELP,
                error=description
            )
        
        self.logger.info(f"Task {task_id} status changed to {status}: {description}")