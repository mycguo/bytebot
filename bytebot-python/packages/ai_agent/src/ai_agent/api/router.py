"""API router for AI agent endpoints."""

import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from shared.models.task import Task, TaskStatus, TaskPriority, TaskType
from shared.database.session import get_db_session_dependency
from ..services.task_processor import TaskProcessor
from ..services.task_service import TaskService


router = APIRouter()
logger = logging.getLogger(__name__)


class CreateTaskRequest(BaseModel):
    """Request model for creating a new task."""
    description: str = Field(..., description="Task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority") 
    type: TaskType = Field(default=TaskType.IMMEDIATE, description="Task type")
    model: Dict[str, Any] = Field(..., description="AI model configuration")


class TaskResponse(BaseModel):
    """Response model for task operations."""
    id: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    type: TaskType
    created_at: str
    updated_at: str


def get_task_service(db=Depends(get_db_session_dependency)) -> TaskService:
    """Dependency to get task service."""
    return TaskService(db)


def get_task_processor() -> TaskProcessor:
    """Dependency to get task processor."""
    return TaskProcessor()


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_request: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    task_service: TaskService = Depends(get_task_service),
    task_processor: TaskProcessor = Depends(get_task_processor)
):
    """Create a new task and start processing it."""
    try:
        # Create task in database
        task = await task_service.create_task(
            description=task_request.description,
            priority=task_request.priority,
            type=task_request.type,
            model=task_request.model
        )
        
        logger.info(f"Created task {task.id}: {task.description}")
        
        # Start processing in background for immediate tasks
        if task.type == TaskType.IMMEDIATE:
            background_tasks.add_task(task_processor.process_task, str(task.id))
        
        return TaskResponse(
            id=str(task.id),
            description=task.description,
            status=task.status,
            priority=task.priority,
            type=task.type,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    limit: int = 50,
    offset: int = 0,
    status: TaskStatus = None,
    task_service: TaskService = Depends(get_task_service)
):
    """List tasks with optional filtering."""
    try:
        tasks = await task_service.list_tasks(
            limit=limit,
            offset=offset, 
            status=status
        )
        
        return [
            TaskResponse(
                id=str(task.id),
                description=task.description,
                status=task.status,
                priority=task.priority,
                type=task.type,
                created_at=task.created_at.isoformat(),
                updated_at=task.updated_at.isoformat(),
            )
            for task in tasks
        ]
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service)
):
    """Get a specific task by ID."""
    try:
        task = await task_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            id=str(task.id),
            description=task.description,
            status=task.status,
            priority=task.priority,
            type=task.type,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.post("/tasks/{task_id}/process")
async def process_task(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    task_processor: TaskProcessor = Depends(get_task_processor)
):
    """Manually trigger task processing."""
    try:
        background_tasks.add_task(task_processor.process_task, str(task_id))
        return {"message": f"Task {task_id} processing started"}
        
    except Exception as e:
        logger.error(f"Error starting task processing for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.post("/tasks/{task_id}/abort")
async def abort_task(
    task_id: UUID,
    task_processor: TaskProcessor = Depends(get_task_processor)
):
    """Abort task processing."""
    try:
        await task_processor.abort_task(str(task_id))
        return {"message": f"Task {task_id} processing aborted"}
        
    except Exception as e:
        logger.error(f"Error aborting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to abort task: {str(e)}")


@router.get("/tasks/{task_id}/messages")
async def get_task_messages(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service)
):
    """Get messages for a specific task."""
    try:
        task = await task_service.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        messages = await task_service.get_task_messages(task_id)
        return {
            "task_id": str(task_id),
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role.value,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: UUID,
    task_service: TaskService = Depends(get_task_service)
):
    """Delete a specific task."""
    try:
        success = await task_service.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": f"Task {task_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@router.delete("/tasks")
async def clear_all_tasks(
    status: TaskStatus = None,
    task_service: TaskService = Depends(get_task_service)
):
    """Clear all tasks, optionally filtered by status."""
    try:
        deleted_count = await task_service.clear_all_tasks(status)
        
        if status:
            return {"message": f"Deleted {deleted_count} tasks with status {status}"}
        else:
            return {"message": f"Deleted {deleted_count} tasks"}
        
    except Exception as e:
        logger.error(f"Error clearing tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear tasks: {str(e)}")


@router.get("/processor/status")
async def get_processor_status(
    task_processor: TaskProcessor = Depends(get_task_processor)
):
    """Get current processor status."""
    return {
        "is_running": task_processor.is_running(),
        "current_task_id": task_processor.get_current_task_id()
    }