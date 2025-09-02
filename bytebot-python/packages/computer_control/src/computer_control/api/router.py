"""API router for computer control endpoints."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from pydantic import ValidationError

from shared.types.computer_action import ComputerAction
from ..computer_use.service import ComputerUseService


router = APIRouter()
logger = logging.getLogger(__name__)


def get_computer_use_service() -> ComputerUseService:
    """Dependency to get computer use service."""
    return ComputerUseService()


@router.post("/computer-use", response_model=Dict[str, Any])
async def computer_action(
    action_data: ComputerAction,
    service: ComputerUseService = Depends(get_computer_use_service)
) -> Dict[str, Any]:
    """Execute computer action.
    
    Handles all computer automation actions like mouse clicks,
    keyboard input, screenshots, etc.
    """
    try:
        # Log action without sensitive data
        action_copy = action_data.model_copy()
        if hasattr(action_copy, 'action') and action_copy.action == 'write_file':
            if hasattr(action_copy, 'data'):
                action_copy.data = "base64 data"
        
        logger.info(f"Computer action request: {action_copy}")
        
        result = await service.execute_action(action_data)
        return result if result is not None else {"success": True}
        
    except ValidationError as e:
        logger.error(f"Validation error in computer action: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid action data: {e}")
    
    except Exception as e:
        logger.error(f"Error executing computer action: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to execute computer action: {str(e)}"
        )


# Legacy compatibility endpoint (matches TypeScript version)
@router.post("/computer-use/")
async def computer_action_legacy(
    action_data: ComputerAction,
    service: ComputerUseService = Depends(get_computer_use_service)
) -> Dict[str, Any]:
    """Legacy endpoint for computer actions."""
    return await computer_action(action_data, service)