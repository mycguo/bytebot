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
        
        max_iterations = 12  # Prevent infinite loops (reduced from 20)
        iteration = 0
        
        # Loop detection variables
        screenshot_count = 0
        max_consecutive_screenshots = 2  # Reduced from 3 to 2
        last_actions = []
        max_action_history = 5
        
        while iteration < max_iterations:
            if abort_event.is_set():
                raise AgentInterrupt("Task processing was aborted")
            
            iteration += 1
            self.logger.debug(f"Task {task.id} - Iteration {iteration}")
            
            # Get model configuration from task
            model_config = task.model if hasattr(task, 'model') and task.model else {
                "name": "claude-sonnet-4-20250514"
            }
            
            try:
                # Call real AI provider
                response = await self.ai_provider.generate_message(
                    system_prompt=AGENT_SYSTEM_PROMPT,
                    messages=messages,
                    model=model_config.get("name", "claude-3-5-sonnet-20240620"),
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
                current_iteration_actions = []
                
                for block in response.content_blocks:
                    if isinstance(block, ToolUseContentBlock):
                        if is_computer_tool_use_content_block(block):
                            has_computer_tools = True
                            
                            # Check if this is a blocked screenshot
                            is_blocked_screenshot = False
                            
                            # Track screenshot usage for loop detection
                            if block.name == "computer_screenshot":
                                screenshot_count += 1
                                if screenshot_count > max_consecutive_screenshots:
                                    self.logger.warning(f"Task {task.id} taking too many consecutive screenshots ({screenshot_count}), adding guidance")
                                    
                                    # Add strong guidance message instead of executing more screenshots
                                    guidance_result = ToolResultContentBlock(
                                        type=MessageContentType.TOOL_RESULT,
                                        tool_use_id=block.id,
                                        content=[
                                            TextContentBlock(
                                                type=MessageContentType.TEXT,
                                                text="SCREENSHOT BLOCKED: You've taken too many screenshots without taking action. You MUST now use interaction tools to complete your task:\n- computer_click_mouse: Click on elements\n- computer_type_text: Type text into fields\n- computer_paste_text: Paste URLs or text\n- set_task_status: Mark task as completed\n\nFor the gmail.com task: Click the address bar and type 'gmail.com' or use computer_paste_text. NO MORE SCREENSHOTS until you take action!"
                                            )
                                        ]
                                    )
                                    tool_results.append(guidance_result)
                                    is_blocked_screenshot = True
                            else:
                                screenshot_count = 0  # Reset if other tool used
                            
                            # Only execute the tool if it's not a blocked screenshot
                            if not is_blocked_screenshot:
                                # Track action for repetition detection
                                action_key = f"{block.name}_{str(block.input)}"
                                current_iteration_actions.append(action_key)
                                
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
                    
                # Update action history for repetition detection
                if current_iteration_actions:
                    last_actions.extend(current_iteration_actions)
                    if len(last_actions) > max_action_history:
                        last_actions = last_actions[-max_action_history:]
                    
                    # Check for action repetition
                    if len(set(last_actions)) <= 2 and len(last_actions) >= 4:
                        self.logger.warning(f"Task {task.id} appears to be repeating actions")
                        # Add guidance about task completion
                        guidance_response = [
                            TextContentBlock(
                                type=MessageContentType.TEXT,
                                text=f"ACTION LOOP DETECTED: You are repeating similar actions for task '{task.description}'. You must now take a different action:\n\n1. If Firefox is open and you need to navigate to gmail.com:\n   - Click the address bar\n   - Type or paste 'gmail.com'\n   - Press Enter\n\n2. If the task is complete, use set_task_status tool with status='completed'\n\n3. If you're stuck, use set_task_status with status='needs_help'\n\nSTOP repeating the same actions!"
                            )
                        ]
                        await task_service.add_message(
                            task_id=task.id,
                            content=[block.model_dump() for block in guidance_response],
                            role=Role.ASSISTANT
                        )
                        break
                
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
                
                # Rate limiting: add delay between iterations 
                if iteration > 5:  # After 5 iterations, increase delay
                    delay = min(1.0, 0.2 * (iteration - 5))  # Exponential backoff, max 1 second
                    self.logger.debug(f"Task {task.id} iteration {iteration}: adding {delay}s delay")
                    await asyncio.sleep(delay)
                else:
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
            self.logger.warning(f"Task {task.id} reached maximum iterations ({max_iterations}), likely stuck in loop")
            
            # Add final guidance message 
            final_guidance = [
                TextContentBlock(
                    type=MessageContentType.TEXT,
                    text="Task reached maximum iterations. This usually indicates the AI got stuck in a loop. The task has been automatically stopped."
                )
            ]
            await task_service.add_message(
                task_id=task.id,
                content=[block.model_dump() for block in final_guidance],
                role=Role.ASSISTANT
            )
            
            # Mark task as failed due to loop
            await task_service.update_task_status(
                task.id,
                TaskStatus.FAILED,
                error=f"Task stopped after {max_iterations} iterations - likely stuck in loop"
            )

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