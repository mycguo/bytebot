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
    elif page == "Settings":
        render_settings_page()


def render_combined_page():
    """Render the combined tasks and desktop page."""
    # Create columns with 1/3 for tasks and 2/3 for desktop
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📝 Tasks")
        
        # Task Creator
        with st.expander("➕ Create New Task", expanded=True):
            render_task_creator()
        
        # Task List
        st.markdown("### 📋 Task List")
        render_task_list()
    
    with col2:
        st.subheader("🖥️ Virtual Desktop")
        render_desktop_viewer()


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


if __name__ == "__main__":
    main()