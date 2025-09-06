"""Main Streamlit application for Bytebot Web UI."""

import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

from web_ui.utils.api_client import APIClient
from web_ui.utils.async_utils import AsyncRunner
from web_ui.components.task_creator import render_task_creator
from web_ui.components.task_list import render_task_list
from web_ui.components.desktop_viewer import render_desktop_viewer
from web_ui.components.live_desktop_view import render_live_desktop_view, handle_live_action_results
from web_ui.components.sidebar import render_sidebar


def main():
    """Main Streamlit application."""
    # Configure page
    st.set_page_config(
        page_title="Bytebot - AI Desktop Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()
    
    if "async_runner" not in st.session_state:
        st.session_state.async_runner = AsyncRunner()
        
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Tasks & Desktop"
    
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = True
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    .task-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .status-pending { background-color: #fef3c7; color: #92400e; }
    .status-running { background-color: #dbeafe; color: #1e40af; }
    .status-completed { background-color: #d1fae5; color: #065f46; }
    .status-failed { background-color: #fee2e2; color: #dc2626; }
    .status-cancelled { background-color: #f3f4f6; color: #4b5563; }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Bytebot - AI Desktop Agent</h1>
        <p>Create tasks, watch AI work, and control your virtual desktop</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    page = render_sidebar()
    st.session_state.current_page = page
    
    # Main content based on selected page
    if page == "Tasks & Desktop":
        render_combined_page()
    elif page == "Live Desktop View":
        render_live_desktop_page()
    elif page == "Settings":
        render_settings_page()


def render_combined_page():
    """Render the combined tasks and desktop page."""
    # Task Creator in expander
    with st.expander("➕ Create New Task", expanded=True):
        render_task_creator()
    
    # Add desktop viewer first
    st.markdown("---")
    render_desktop_viewer_section_main()
    
    # Add spacing before Tasks & Desktop section
    st.markdown("---")
    
    # Tasks & Desktop section moved below Virtual Desktop
    st.markdown("### 📋 Tasks & Desktop")
    
    # Filter and action controls
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"], key="main_status_filter")
    with col2:
        limit = st.selectbox("Show", [10, 25, 50, 100], index=1, key="main_limit")
    with col3:
        if st.button("🔄 Refresh All", use_container_width=True, key="main_refresh"):
            trigger_load_tasks_main(status_filter, limit)

    # Trigger initial load
    if "main_load_tasks_future" not in st.session_state and "main_tasks" not in st.session_state:
        st.session_state.main_tasks = []
        trigger_load_tasks_main(status_filter, limit)

    # Render tasks or loading state
    render_main_task_loading_state()


def render_tasks_page():
    """Render the main tasks page."""
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("📝 Create New Task")
        render_task_creator()
    
    with col2:
        st.subheader("📋 Task List")
        render_task_list()


def render_desktop_page():
    """Render the desktop viewer page."""
    st.subheader("🖥️ Virtual Desktop")
    render_desktop_viewer()


def render_live_desktop_page():
    """Render the live desktop view page."""
    # Handle any pending action results first
    handle_live_action_results()
    
    # Main title
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2>🖥️ Live Desktop View</h2>
        <p style="color: #666; margin-top: 0.5rem;">
            Real-time view of your virtual desktop with interactive controls
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render the live desktop view component
    render_live_desktop_view()


def render_settings_page():
    """Render the settings page."""
    st.subheader("⚙️ Settings")
    
    # API Configuration
    with st.expander("🔌 API Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            agent_url = st.text_input(
                "AI Agent Service URL", 
                value="http://localhost:9996",
                help="URL for the AI agent service"
            )
            
        with col2:
            computer_url = st.text_input(
                "Computer Control Service URL",
                value="http://localhost:9995", 
                help="URL for the computer control service"
            )
        
        if st.button("💾 Save API Configuration"):
            st.session_state.api_client.agent_base_url = agent_url
            st.session_state.api_client.computer_base_url = computer_url
            st.success("✅ API configuration saved!")
    
    # Display Settings
    with st.expander("🎨 Display Settings"):
        auto_refresh = st.checkbox(
            "Auto-refresh task list",
            value=st.session_state.auto_refresh,
            help="Automatically refresh the task list every 5 seconds"
        )
        st.session_state.auto_refresh = auto_refresh
        
        refresh_interval = st.slider(
            "Refresh interval (seconds)",
            min_value=1,
            max_value=30,
            value=5,
            help="How often to refresh the task list"
        )
        st.session_state.refresh_interval = refresh_interval
    
    # System Status
    with st.expander("📊 System Status"):
        if st.button("🔍 Check Services Status"):
            check_services_status()
        
        render_service_status()


def check_services_status():
    """Triggers async checks for service statuses."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    st.session_state.agent_status_future = runner.run(api_client.get("/health"))
    st.session_state.computer_status_future = runner.run(api_client.get_computer("/health"))
    st.rerun()

def render_service_status():
    """Renders the status of services based on futures in session state."""
    col1, col2 = st.columns(2)

    with col1:
        st.write("**AI Agent Service:**")
        if 'agent_status_future' in st.session_state:
            future = st.session_state.agent_status_future
            if future.done():
                try:
                    response = future.result()
                    st.success("✅ Online")
                    st.json(response)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                del st.session_state.agent_status_future
            else:
                st.spinner("Checking...")
        else:
            st.write("Click button to check status.")

    with col2:
        st.write("**Computer Control Service:**")
        if 'computer_status_future' in st.session_state:
            future = st.session_state.computer_status_future
            if future.done():
                try:
                    response = future.result()
                    st.success("✅ Online")
                    st.json(response)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                del st.session_state.computer_status_future
            else:
                st.spinner("Checking...")
        else:
            st.write("Click button to check status.")


def trigger_load_tasks_main(status_filter: str, limit: int):
    """Triggers an asynchronous load of the task list for main page."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    status = None if status_filter == "All" else status_filter
    future = runner.run(api_client.get_tasks(limit=limit, status=status))
    st.session_state.main_load_tasks_future = future
    st.rerun()


def render_main_task_loading_state():
    """Renders the task list or a loading spinner for main page."""
    if 'main_load_tasks_future' in st.session_state:
        future = st.session_state.main_load_tasks_future
        if future.done():
            try:
                tasks = future.result()
                st.session_state.main_tasks = tasks if tasks else []
                if not st.session_state.main_tasks:
                    st.info("📭 No tasks found.")
            except Exception as e:
                st.error(f"❌ Error loading tasks: {e}")
                st.session_state.main_tasks = []
            del st.session_state.main_load_tasks_future
            st.rerun()
        else:
            st.spinner("Loading tasks...")
            return

    if "main_tasks" not in st.session_state:
        st.session_state.main_tasks = []

    st.write(f"📋 **{len(st.session_state.main_tasks)} tasks**")
    for task in st.session_state.main_tasks:
        render_main_task_card(task)


def render_main_task_card(task):
    """Render a single task card for main page."""
    from datetime import datetime
    
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

        # Check for ongoing action for this specific task
        if "main_task_action_futures" in st.session_state and task_id in st.session_state.main_task_action_futures:
            future = st.session_state.main_task_action_futures[task_id]["future"]
            action_name = st.session_state.main_task_action_futures[task_id]["name"]
            
            if future.done():
                try:
                    future.result()
                    st.success(f"✅ {action_name} successful!")
                    trigger_load_tasks_main("All", 25) # Refresh list after action
                except Exception as e:
                    st.error(f"❌ {action_name} failed: {e}")
                del st.session_state.main_task_action_futures[task_id]
                st.rerun()
            else:
                st.spinner(f"{action_name} in progress...")
        else:
            # Simple action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if status == "PENDING" and st.button("▶️ Start", key=f"main_start_{task_id}", use_container_width=True):
                    trigger_main_task_action("Start", task_id, "process_task")
            with col2:
                if status == "RUNNING" and st.button("⏹️ Stop", key=f"main_stop_{task_id}", use_container_width=True):
                    trigger_main_task_action("Stop", task_id, "abort_task")
            with col3:
                if st.button("🗑️ Delete", key=f"main_delete_{task_id}", use_container_width=True):
                    trigger_main_task_action("Delete", task_id, "delete_task")
        
        st.markdown("---")


def trigger_main_task_action(action_name: str, task_id: str, method_name: str):
    """Triggers a task action for main page."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    method_to_call = getattr(api_client, method_name)
    future = runner.run(method_to_call(task_id))
    
    # Use separate state for main page actions
    if "main_task_action_futures" not in st.session_state:
        st.session_state.main_task_action_futures = {}
    
    st.session_state.main_task_action_futures[task_id] = {"name": action_name, "future": future}
    st.rerun()


def render_desktop_viewer_section_main():
    """Render desktop viewer section for main page."""
    from web_ui.components.desktop_viewer import trigger_screenshot, render_screenshot_result, display_desktop_screenshot
    
    st.markdown("### 🖥️ Virtual Desktop")
    
    # Simple screenshot button
    if st.button("📷 Take Screenshot", use_container_width=True, key="main_desktop_screenshot"):
        trigger_screenshot()
    
    # Handle screenshot results and display
    render_screenshot_result()
    display_desktop_screenshot()


if __name__ == "__main__":
    main()