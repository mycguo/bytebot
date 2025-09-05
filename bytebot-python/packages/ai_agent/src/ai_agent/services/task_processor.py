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
    is_create_task_tool_use_block,
)

from .task_service import TaskService
from ..models.constants import AGENT_SYSTEM_PROMPT
from ..models.agent_types import AgentInterrupt
from ..providers.anthropic import AnthropicService
from ..providers.openai_provider import OpenAIService


class TaskProcessor:
    """Processes tasks using AI agents."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_task_id: Optional[str] = None
        self.is_processing = False
        self.abort_controllers: Dict[str, asyncio.Event] = {}
        
        # Computer control service URL - use environment variable
        self.computer_control_url = os.getenv("COMPUTER_CONTROL_URL", "http://computer-control:9995")
        
        # Initialize AI provider - use OpenAI first due to Anthropic credit issues  
        self.ai_provider = None
        try:
            self.ai_provider = OpenAIService()
            self.logger.info("OpenAI AI provider initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenAI provider: {e}")
            
        # If OpenAI fails, try Anthropic as fallback
        if not self.ai_provider:
            try:
                self.ai_provider = AnthropicService()
                self.logger.info("Anthropic AI provider initialized as fallback")
            except Exception as e:
                self.logger.error(f"Failed to initialize Anthropic provider: {e}")
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
        
        max_iterations = 25  # Increased from 12 to match TypeScript behavior
        iteration = 0
        
        # Loop detection variables
        screenshot_count = 0
        # Increase screenshot tolerance for browser navigation tasks
        if any(keyword in task.description.lower() for keyword in ["browser", "firefox", "chrome", "navigate", "go to", "gmail", "website", "url"]):
            max_consecutive_screenshots = 8  # More lenient for browser tasks
        else:
            max_consecutive_screenshots = 4  # Standard for other tasks
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
            
            # Use appropriate model based on provider
            if isinstance(self.ai_provider, OpenAIService):
                model_name = "gpt-4o"  # Use OpenAI's latest model
            else:
                model_name = model_config.get("name", "claude-3-5-sonnet-20240620")
            
            try:
                # Call real AI provider
                response = await self.ai_provider.generate_message(
                    system_prompt=AGENT_SYSTEM_PROMPT,
                    messages=messages,
                    model=model_name,
                    use_tools=True,
                    signal=abort_event
                )
                
                # Log AI conversation for debugging
                self.logger.info(f"Task {task.id} - Iteration {iteration}: AI Response with {len(response.content_blocks)} blocks")
                for i, block in enumerate(response.content_blocks):
                    if hasattr(block, 'text') and block.text:
                        self.logger.info(f"Task {task.id} - Block {i}: TEXT: {block.text[:200]}...")
                    elif hasattr(block, 'name') and block.name:
                        self.logger.info(f"Task {task.id} - Block {i}: TOOL: {block.name} with input: {block.input}")
                
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
                            
                            # Track screenshot usage for loop detection (more lenient like TypeScript)
                            if block.name == "computer_screenshot":
                                screenshot_count += 1
                                if screenshot_count > max_consecutive_screenshots:
                                    self.logger.warning(f"Task {task.id} taking many consecutive screenshots ({screenshot_count}), adding gentle guidance")
                                    
                                    # Provide context-aware guidance instead of blocking (like TypeScript behavior)
                                    guidance_text = f"You have taken {screenshot_count} consecutive screenshots. Continue with the next action to complete the full task:\n"
                                    if any(keyword in task.description.lower() for keyword in ["firefox", "browser", "navigate", "go to", "gmail", "website", "url"]):
                                        guidance_text += "For browser navigation tasks:\n"
                                        guidance_text += "1. Launch Firefox: computer_application with application='firefox'\n"
                                        guidance_text += "2. Wait 3-4 seconds for Firefox to load completely\n" 
                                        guidance_text += "3. Click address bar (around x=640, y=80): computer_click_mouse\n"
                                        guidance_text += "4. Type the URL (e.g., 'gmail.com'): computer_type_text\n"
                                        guidance_text += "5. Press Enter: computer_type_keys with keys=['Return']\n"
                                        guidance_text += "6. Wait for page to load, then verify you reached the destination\n"
                                        guidance_text += "IMPORTANT: Complete ALL steps - don't stop after just launching Firefox!"
                                    else:
                                        guidance_text += "Available actions:\n- computer_click_mouse: Click on elements\n- computer_type_text: Type text\n- computer_application: Launch apps\n- set_task_status: Complete or report status"
                                    
                                    guidance_result = ToolResultContentBlock(
                                        type=MessageContentType.TOOL_RESULT,
                                        tool_use_id=block.id,
                                        content=[
                                            TextContentBlock(
                                                type=MessageContentType.TEXT,
                                                text=guidance_text
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
                                self.logger.info(f"Task {task.id} - Executing tool: {block.name} with input: {block.input}")
                                result = await self._execute_computer_tool(block)
                                tool_results.append(result)
                                self.logger.info(f"Task {task.id} - Tool result: {result.content[0].text if result.content else 'No content'}")
                                
                                # Auto-screenshot after non-screenshot actions like TypeScript
                                if block.name != "computer_screenshot":
                                    try:
                                        # Wait briefly for UI to settle (like TypeScript: 750ms)
                                        await asyncio.sleep(0.75)
                                        
                                        # Take automatic screenshot
                                        auto_screenshot_data = {
                                            "action": "screenshot"
                                        }
                                        
                                        async with httpx.AsyncClient() as client:
                                            response = await client.post(
                                                f"{self.computer_control_url}/computer-use",
                                                json=auto_screenshot_data,
                                                timeout=30.0
                                            )
                                            if response.status_code == 200:
                                                screenshot_result = response.json()
                                                if "data" in screenshot_result:
                                                    from shared.types.message_content import ImageContentBlock, ImageSource
                                                    image_block = ImageContentBlock(
                                                        type=MessageContentType.IMAGE,
                                                        source=ImageSource(
                                                            media_type="image/png",
                                                            type="base64",
                                                            data=screenshot_result["data"]
                                                        )
                                                    )
                                                    # Add image to the existing tool result
                                                    result.content.append(image_block)
                                                    
                                    except Exception as e:
                                        self.logger.debug(f"Auto-screenshot after {block.name} failed: {e}")
                                        # Don't fail the task if auto-screenshot fails
                        elif is_create_task_tool_use_block(block):
                            # Handle task creation
                            await self._handle_create_task(task_service, block)
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
                    
                    # Check for action repetition - but be more lenient for browser tasks
                    is_browser_task = any(keyword in task.description.lower() for keyword in ["firefox", "browser", "chrome", "navigate", "gmail", "website", "url"])
                    repetition_threshold = 6 if is_browser_task else 4  # More lenient for browser tasks
                    
                    if len(set(last_actions)) <= 2 and len(last_actions) >= repetition_threshold:
                        self.logger.warning(f"Task {task.id} appears to be repeating actions: {last_actions}")
                        # Add guidance about task completion but don't break - let it continue with guidance
                        guidance_response = [
                            TextContentBlock(
                                type=MessageContentType.TEXT,
                                text=f"ACTION LOOP DETECTED: You are repeating similar actions for task '{task.description}'. Recent actions: {last_actions}\n\nYou must now take a DIFFERENT action:\n\n1. If Firefox is open and you need to navigate somewhere:\n   - Click the address bar (usually around coordinates 640, 80)\n   - Type the destination URL\n   - Press Enter to navigate\n\n2. If Firefox needs to be launched first:\n   - Use computer_application with application='firefox'\n   - Wait a few seconds for it to load\n   - Then proceed with navigation\n\n3. If the task is actually complete, use set_task_status tool with status='completed'\n\n4. If you're stuck, use set_task_status with status='needs_help'\n\nSTOP repeating the same actions! Take a DIFFERENT action now!"
                            )
                        ]
                        await task_service.add_message(
                            task_id=task.id,
                            content=[block.model_dump() for block in guidance_response],
                            role=Role.ASSISTANT
                        )
                        # Clear action history to give it a fresh start instead of breaking
                        last_actions = []
                        # Add one more iteration chance after guidance
                        if iteration >= max_iterations - 3:  # Give a few more chances after guidance
                            max_iterations += 3
                
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
        self.logger.info(f"Executing computer tool: {tool_block.name} with input: {tool_block.input}")
        
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

    async def _handle_create_task(self, task_service: TaskService, tool_block: ToolUseContentBlock):
        """Handle create task tool."""
        task_input = tool_block.input
        description = task_input.get("description")
        priority = task_input.get("priority", "medium")
        
        if not description:
            self.logger.error("Create task called without description")
            return
        
        # Create new task
        new_task = await task_service.create_task(
            description=description,
            priority=priority
        )
        
        self.logger.info(f"Created new subtask {new_task.id}: {description} (priority: {priority})")