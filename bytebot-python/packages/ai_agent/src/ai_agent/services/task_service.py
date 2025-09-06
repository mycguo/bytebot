"""Task service for database operations."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from shared.models.task import Task, TaskStatus, TaskPriority, TaskType, Role
from shared.models.message import Message


class TaskService:
    """Service for task database operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        type: TaskType = TaskType.IMMEDIATE,
        model: Dict[str, Any] = None
    ) -> Task:
        """Create a new task."""
        if model is None:
            model = {
                "provider": "anthropic",
                "name": "claude-opus-4-1-20250805", 
                "title": "Claude Opus 4.1"
            }
        
        task = Task(
            description=description,
            priority=priority,
            type=type,
            model=model,
            status=TaskStatus.PENDING,
            control=Role.ASSISTANT,
            created_by=Role.USER
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        self.logger.info(f"Created task {task.id}: {description[:100]}...")
        return task

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """Get a task by ID."""
        return self.db.query(Task).filter(Task.id == task_id).first()

    async def list_tasks(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """List tasks with optional filtering."""
        query = self.db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        
        query = query.order_by(desc(Task.created_at))
        query = query.offset(offset).limit(limit)
        
        return query.all()

    async def update_task_status(
        self,
        task_id: UUID,
        status: TaskStatus,
        error: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """Update task status."""
        task = await self.get_task(task_id)
        if not task:
            return None
        
        task.status = status
        task.updated_at = datetime.utcnow()
        
        if error:
            task.error = error
        
        if result:
            task.result = result
            
        if status == TaskStatus.RUNNING:
            task.executed_at = datetime.utcnow()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(task)
        
        self.logger.info(f"Updated task {task_id} status to {status}")
        return task

    async def add_message(
        self,
        task_id: UUID,
        content: List[Dict[str, Any]],
        role: Role = Role.ASSISTANT
    ) -> Optional[Message]:
        """Add a message to a task."""
        task = await self.get_task(task_id)
        if not task:
            return None
        
        message = Message(
            task_id=task_id,
            content=content,
            role=role
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        self.logger.debug(f"Added message to task {task_id}")
        return message

    async def get_task_messages(self, task_id: UUID) -> List[Message]:
        """Get all messages for a task."""
        return self.db.query(Message).filter(
            Message.task_id == task_id
        ).order_by(Message.created_at).all()

    async def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks."""
        return self.db.query(Task).filter(
            and_(
                Task.status == TaskStatus.PENDING,
                Task.type == TaskType.IMMEDIATE
            )
        ).order_by(Task.priority.desc(), Task.created_at).all()

    async def delete_task(self, task_id: UUID) -> bool:
        """Delete a task by ID."""
        task = await self.get_task(task_id)
        if not task:
            return False
        
        # Delete associated messages first
        self.db.query(Message).filter(Message.task_id == task_id).delete()
        
        # Delete the task
        self.db.delete(task)
        self.db.commit()
        
        self.logger.info(f"Deleted task {task_id}")
        return True

    async def clear_all_tasks(self, status_filter: Optional[TaskStatus] = None) -> int:
        """Clear all tasks, optionally filtered by status."""
        # Build base query
        query = self.db.query(Task)
        
        if status_filter:
            query = query.filter(Task.status == status_filter)
        
        # Get all task IDs to delete
        task_ids = [task.id for task in query.all()]
        
        if not task_ids:
            return 0
        
        # Delete associated messages first
        for task_id in task_ids:
            self.db.query(Message).filter(Message.task_id == task_id).delete()
        
        # Delete tasks
        deleted_count = query.delete()
        self.db.commit()
        
        self.logger.info(f"Deleted {deleted_count} tasks")
        return deleted_count