"""Task list component."""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any


def render_task_list():
    """Render the task list interface."""
    
    # Auto-refresh setup
    if st.session_state.get("auto_refresh", True):
        # This would be replaced with streamlit-autorefresh in a full implementation
        refresh_placeholder = st.empty()
        with refresh_placeholder:
            if st.button("🔄 Refresh", key="manual_refresh"):
                st.rerun()
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"],
            index=0
        )
    
    with col2:
        limit = st.selectbox(
            "Show",
            [10, 25, 50, 100],
            index=1
        )
    
    with col3:
        if st.button("🗑️ Clear All", help="Clear all tasks"):
            clear_all_tasks_with_confirmation()
    
    # Load and display tasks
    load_and_display_tasks(status_filter, limit)


def load_and_display_tasks(status_filter: str, limit: int):
    """Load tasks from API and display them."""
    try:
        api_client = st.session_state.api_client
        
        # Determine status parameter
        status_param = None if status_filter == "All" else status_filter
        
        # Load tasks
        with st.spinner("Loading tasks..."):
            tasks = asyncio.run(api_client.get_tasks(limit=limit, status=status_param))
        
        if not tasks:
            st.info("📭 No tasks found or unable to connect to AI Agent service.")
            return
        
        if len(tasks) == 0:
            st.info("📭 No tasks found matching the current filter.")
            return
        
        # Display tasks
        st.write(f"📋 **{len(tasks)} tasks** (showing max {limit})")
        
        for task in tasks:
            render_task_card(task)
            
    except Exception as e:
        st.error(f"❌ Error loading tasks: {str(e)}")


def render_task_card(task: Dict[str, Any]):
    """Render a single task card."""
    task_id = task.get("id", "unknown")
    description = task.get("description", "No description")
    status = task.get("status", "UNKNOWN")
    priority = task.get("priority", "MEDIUM")
    created_at = task.get("created_at", "")
    
    # Status color mapping
    status_colors = {
        "PENDING": "🟡",
        "RUNNING": "🔵", 
        "COMPLETED": "🟢",
        "FAILED": "🔴",
        "CANCELLED": "⚫",
        "NEEDS_HELP": "🟠"
    }
    
    # Priority color mapping
    priority_colors = {
        "LOW": "🔹",
        "MEDIUM": "🔸", 
        "HIGH": "🔶",
        "URGENT": "🔺"
    }
    
    status_icon = status_colors.get(status, "⚪")
    priority_icon = priority_colors.get(priority, "🔸")
    
    # Format created time
    created_time = ""
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            created_time = dt.strftime("%m/%d %H:%M")
        except:
            created_time = created_at[:16] if len(created_at) > 16 else created_at
    
    # Task card container
    with st.container():
        st.markdown(f"""
        <div class="task-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                <div style="flex: 1;">
                    <h4 style="margin: 0; color: #1f2937;">{description[:100]}{'...' if len(description) > 100 else ''}</h4>
                </div>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <span>{priority_icon} {priority}</span>
                    <span>{status_icon} {status}</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.875rem; color: #6b7280;">
                <span>📅 {created_time}</span>
                <span>🆔 {task_id[:8]}...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("👁️ View", key=f"view_{task_id}"):
                show_task_details(task)
        
        with col2:
            if status == "PENDING" and st.button("▶️ Start", key=f"start_{task_id}"):
                process_task(task_id)
        
        with col3:
            if status == "RUNNING" and st.button("⏹️ Stop", key=f"stop_{task_id}"):
                abort_task(task_id)
        
        with col4:
            if st.button("🔄 Refresh", key=f"refresh_{task_id}"):
                refresh_single_task(task_id)
        
        with col5:
            if st.button("🗑️ Delete", key=f"delete_{task_id}"):
                delete_single_task(task_id)
        
        st.markdown("---")


def show_task_details(task: Dict[str, Any]):
    """Show detailed task information in a modal-like display."""
    with st.expander(f"📋 Task Details: {task.get('id', 'Unknown')[:8]}...", expanded=True):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Description:**")
            st.write(task.get("description", "No description"))
            
            st.write("**Status:**")
            st.write(task.get("status", "Unknown"))
            
            st.write("**Priority:**")
            st.write(task.get("priority", "Unknown"))
        
        with col2:
            st.write("**Created:**")
            st.write(task.get("created_at", "Unknown"))
            
            st.write("**Updated:**") 
            st.write(task.get("updated_at", "Unknown"))
            
            st.write("**Type:**")
            st.write(task.get("type", "Unknown"))
        
        # Full task JSON
        if st.checkbox("Show raw data", key=f"raw_{task.get('id')}"):
            st.json(task)


def process_task(task_id: str):
    """Process a specific task."""
    try:
        with st.spinner("Starting task processing..."):
            api_client = st.session_state.api_client
            result = asyncio.run(api_client.process_task(task_id))
            
            if result:
                st.success(f"✅ Task {task_id[:8]}... processing started!")
                st.rerun()
            else:
                st.error("❌ Failed to start task processing")
                
    except Exception as e:
        st.error(f"❌ Error processing task: {str(e)}")


def abort_task(task_id: str):
    """Abort a running task."""
    try:
        with st.spinner("Stopping task..."):
            api_client = st.session_state.api_client
            result = asyncio.run(api_client.abort_task(task_id))
            
            if result:
                st.success(f"✅ Task {task_id[:8]}... stopped!")
                st.rerun()
            else:
                st.error("❌ Failed to stop task")
                
    except Exception as e:
        st.error(f"❌ Error stopping task: {str(e)}")


def refresh_single_task(task_id: str):
    """Refresh a single task."""
    try:
        with st.spinner("Refreshing task..."):
            api_client = st.session_state.api_client
            result = asyncio.run(api_client.get_task(task_id))
            
            if result:
                show_task_details(result)
            else:
                st.error("❌ Failed to refresh task")
                
    except Exception as e:
        st.error(f"❌ Error refreshing task: {str(e)}")


def delete_single_task(task_id: str):
    """Delete a single task."""
    try:
        with st.spinner("Deleting task..."):
            api_client = st.session_state.api_client
            result = asyncio.run(api_client.delete_task(task_id))
            
            if result:
                st.success(f"✅ Task {task_id[:8]}... deleted!")
                st.rerun()
            else:
                st.error("❌ Failed to delete task")
                
    except Exception as e:
        st.error(f"❌ Error deleting task: {str(e)}")


def clear_all_tasks_with_confirmation():
    """Clear all tasks with confirmation dialog."""
    try:
        # Show confirmation dialog
        if "confirm_clear_all" not in st.session_state:
            st.session_state.confirm_clear_all = False
        
        if not st.session_state.confirm_clear_all:
            with st.container():
                st.warning("⚠️ Are you sure you want to delete ALL tasks? This action cannot be undone.")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Yes, Delete All", type="primary"):
                        st.session_state.confirm_clear_all = True
                        st.rerun()
                
                with col2:
                    if st.button("❌ Cancel"):
                        st.info("Clear all operation cancelled.")
        else:
            # Perform the deletion
            with st.spinner("Deleting all tasks..."):
                api_client = st.session_state.api_client
                result = asyncio.run(api_client.clear_all_tasks())
                
                if result:
                    message = result.get("message", "All tasks deleted")
                    st.success(f"✅ {message}")
                    st.session_state.confirm_clear_all = False
                    st.rerun()
                else:
                    st.error("❌ Failed to delete all tasks")
                    st.session_state.confirm_clear_all = False
                
    except Exception as e:
        st.error(f"❌ Error clearing all tasks: {str(e)}")
        st.session_state.confirm_clear_all = False