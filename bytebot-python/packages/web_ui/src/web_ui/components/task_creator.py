"""Task creation component."""

import streamlit as st
import asyncio
from typing import Dict, Any


def render_task_creator():
    """Render the task creation interface."""
    
    # Show example tasks first
    render_task_examples()
    
    with st.form("create_task_form", clear_on_submit=True):
        # Task description with example pre-fill
        initial_value = st.session_state.get("example_description", "")
        description = st.text_area(
            "Task Description",
            value=initial_value,
            placeholder="Describe what you want the AI to do...",
            help="Be specific about what you want accomplished",
            height=100
        )
        
        # Clear the example after use
        if "example_description" in st.session_state:
            del st.session_state.example_description
        
        # Priority selection
        priority = st.selectbox(
            "Priority",
            ["LOW", "MEDIUM", "HIGH", "URGENT"],
            index=1,
            help="Task priority level"
        )
        
        # AI Model selection
        col1, col2 = st.columns(2)
        
        with col1:
            provider = st.selectbox(
                "AI Provider",
                ["anthropic", "openai", "google"],
                index=0,
                help="Choose AI provider"
            )
        
        with col2:
            # Model options based on provider
            model_options = {
                "anthropic": [
                    ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet"),
                    ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
                    ("claude-3-opus-20240229", "Claude 3 Opus")
                ],
                "openai": [
                    ("gpt-4o", "GPT-4o"),
                    ("gpt-4o-mini", "GPT-4o Mini"),
                    ("gpt-4-turbo", "GPT-4 Turbo")
                ],
                "google": [
                    ("gemini-2.5-pro", "Gemini 2.5 Pro"),
                    ("gemini-2.5-flash", "Gemini 2.5 Flash")
                ]
            }
            
            model_name, model_title = st.selectbox(
                "Model",
                model_options[provider],
                format_func=lambda x: x[1],
                help="Choose specific model"
            )
        
        # File upload
        uploaded_files = st.file_uploader(
            "Upload Files (Optional)",
            accept_multiple_files=True,
            type=['txt', 'pdf', 'png', 'jpg', 'jpeg', 'csv', 'json'],
            help="Upload files that the AI should process"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Create Task", use_container_width=True)
        
        if submitted and description.strip():
            # Create model configuration
            model_config = {
                "provider": provider,
                "name": model_name,
                "title": model_title
            }
            
            # Create task
            create_task_async(description.strip(), priority, model_config, uploaded_files)
        
        elif submitted and not description.strip():
            st.error("❌ Please provide a task description!")


def create_task_async(description: str, priority: str, model: Dict[str, Any], files=None):
    """Create task asynchronously."""
    try:
        with st.spinner("Creating task..."):
            api_client = st.session_state.api_client
            
            # TODO: Handle file uploads
            if files:
                st.info(f"📁 Files uploaded: {len(files)} (file processing will be added)")
            
            # Create the task
            result = asyncio.run(api_client.create_task(description, priority, model))
            
            if result:
                st.success(f"✅ Task created successfully!")
                st.json(result)
                
                # Trigger refresh of task list
                if "task_list_refresh" not in st.session_state:
                    st.session_state.task_list_refresh = 0
                st.session_state.task_list_refresh += 1
                
            else:
                st.error("❌ Failed to create task. Please check if the AI Agent service is running.")
                
    except Exception as e:
        st.error(f"❌ Error creating task: {str(e)}")


def render_task_examples():
    """Render example tasks for inspiration."""
    with st.expander("💡 Example Tasks"):
        examples = [
            "Take a screenshot of the desktop",
            "Open Firefox and navigate to Wikipedia",
            "Create a new text file with today's date",
            "Search for Python tutorials and bookmark interesting ones",
            "Take screenshots of the top 5 news websites",
            "Read the uploaded document and create a summary"
        ]
        
        for example in examples:
            if st.button(f"📋 {example}", key=f"example_{example}"):
                st.session_state.example_description = example
                st.rerun()