"""Task list and desktop control component."""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def render_task_list():
    """Render the task list interface."""
    # Initialize session state
    if "task_action_futures" not in st.session_state:
        st.session_state.task_action_futures = {}
    if "tasks" not in st.session_state:
        st.session_state.tasks = []

    # Standard task interface (Take Over moved to Live Desktop View)
    render_standard_task_interface()


def render_standard_task_interface():
    """Render the standard task management interface."""
    st.markdown("### 📋 Tasks & Desktop")
    
    # Filter and action controls
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"])
    with col2:
        limit = st.selectbox("Show", [10, 25, 50, 100], index=1)
    with col3:
        if st.button("🔄 Refresh All", use_container_width=True):
            trigger_load_tasks(status_filter, limit)

    # Trigger initial load
    if "load_tasks_future" not in st.session_state and not st.session_state.tasks:
        trigger_load_tasks(status_filter, limit)

    # Render tasks or loading state
    render_task_loading_state()


def render_desktop_viewer_section():
    """Render desktop viewer section in Tasks & Desktop."""
    from .desktop_viewer import render_desktop_viewer
    
    st.markdown("### 🖥️ Desktop Control")
    st.info("💡 **Tip**: For Take Over functionality with input capture, use the **Live Desktop View** section.")
    
    render_desktop_viewer()


def trigger_load_tasks(status_filter: str, limit: int):
    """Triggers an asynchronous load of the task list."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    status = None if status_filter == "All" else status_filter
    future = runner.run(api_client.get_tasks(limit=limit, status=status))
    st.session_state.load_tasks_future = future
    st.rerun()


def render_task_loading_state():
    """Renders the task list or a loading spinner based on the future."""
    if 'load_tasks_future' in st.session_state:
        future = st.session_state.load_tasks_future
        if future.done():
            try:
                tasks = future.result()
                st.session_state.tasks = tasks if tasks else []
                if not st.session_state.tasks:
                    st.info("📭 No tasks found.")
            except Exception as e:
                st.error(f"❌ Error loading tasks: {e}")
                st.session_state.tasks = []
            del st.session_state.load_tasks_future
            st.rerun() # Rerun once more to display the loaded tasks
        else:
            st.spinner("Loading tasks...")
            return

    st.write(f"📋 **{len(st.session_state.tasks)} tasks**")
    for task in st.session_state.tasks:
        render_task_card(task)


def render_task_card(task: Dict[str, Any]):
    """Render a single task card with action buttons or a spinner."""
    task_id = task.get("id", "unknown")
    
    with st.container():
        # Display task info
        description = task.get("description", "No description")
        status = task.get("status", "UNKNOWN")
        created_at = task.get("created_at", "")
        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00')) if created_at else None
        st.markdown(f"**{description}**")
        created_str = dt.strftime("%m/%d %H:%M") if dt else 'N/A'
        st.caption(f"Status: {status} | Created: {created_str} | ID: {task_id[:8]}...")

        # Check for an ongoing action for this specific task
        if task_id in st.session_state.task_action_futures:
            future = st.session_state.task_action_futures[task_id]["future"]
            action_name = st.session_state.task_action_futures[task_id]["name"]
            
            if future.done():
                try:
                    future.result()
                    st.success(f"✅ {action_name} successful!")
                    trigger_load_tasks("All", 25) # Refresh list after action
                except Exception as e:
                    st.error(f"❌ {action_name} failed: {e}")
                del st.session_state.task_action_futures[task_id]
                st.rerun()
            else:
                st.spinner(f"{action_name} in progress...")
        else:
            render_task_actions(task)
        st.markdown("---")


def render_task_actions(task: Dict[str, Any]):
    """Render action buttons for a task."""
    task_id = task["id"]
    status = task["status"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if status == "PENDING" and st.button("▶️ Start", key=f"start_{task_id}", use_container_width=True):
            trigger_task_action("Start", task_id, "process_task")
    with col2:
        if status == "RUNNING" and st.button("⏹️ Stop", key=f"stop_{task_id}", use_container_width=True):
            trigger_task_action("Stop", task_id, "abort_task")
    with col3:
        if st.button("🗑️ Delete", key=f"delete_{task_id}", use_container_width=True):
            trigger_task_action("Delete", task_id, "delete_task")


def trigger_task_action(action_name: str, task_id: str, method_name: str):
    """Triggers a generic, non-blocking action on a task."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    method_to_call = getattr(api_client, method_name)
    future = runner.run(method_to_call(task_id))
    
    st.session_state.task_action_futures[task_id] = {"name": action_name, "future": future}
    st.rerun()