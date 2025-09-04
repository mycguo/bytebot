"""Task creation component."""

import streamlit as st
from typing import Dict, Any, List


def render_task_creator():
    """Render the task creation interface."""
    
    render_task_examples()
    
    with st.form("create_task_form", clear_on_submit=True):
        initial_value = st.session_state.get("example_description", "")
        description = st.text_area(
            "Task Description",
            value=initial_value,
            placeholder="Describe what you want the AI to do...",
            height=100
        )
        priority = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH", "URGENT"], index=1)
        
        col1, col2 = st.columns(2)
        with col1:
            provider = st.selectbox("AI Provider", ["anthropic", "openai", "google"], index=0)
        with col2:
            model_options = {
                "anthropic": [
                    ("claude-sonnet-4-20250514", "Claude 4 Sonnet"),
                    ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet (Invalid)"),
                ],
                "openai": [("gpt-4o", "GPT-4o"), ("gpt-4o-mini", "GPT-4o Mini")],
                "google": [("gemini-2.5-pro", "Gemini 2.5 Pro")]
            }
            model_name, model_title = st.selectbox(
                "Model", model_options[provider], format_func=lambda x: x[1]
            )

        uploaded_files = st.file_uploader(
            "Upload Files (Optional)", accept_multiple_files=True
        )
        
        submitted = st.form_submit_button("🚀 Create Task", use_container_width=True)
        
        if submitted and description.strip():
            if "example_description" in st.session_state:
                del st.session_state.example_description
            
            model_config = {"provider": provider, "name": model_name, "title": model_title}
            trigger_create_task(description.strip(), priority, model_config, uploaded_files)
        
        elif submitted and not description.strip():
            st.error("❌ Please provide a task description!")

    render_create_task_status()


def trigger_create_task(description: str, priority: str, model: Dict[str, Any], files: List[Any]):
    """Trigger the asynchronous creation of a task."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    # TODO: Handle file uploads properly by passing data, not Streamlit objects
    if files:
        st.info(f"📁 Files uploaded: {len(files)} (file processing not implemented yet)")

    future = runner.run(api_client.create_task(description, priority, model))
    st.session_state['create_task_future'] = future
    st.rerun()


def render_create_task_status():
    """Render the status of the task creation future."""
    if 'create_task_future' in st.session_state:
        future = st.session_state['create_task_future']
        
        if future.done():
            try:
                result = future.result()
                st.success("✅ Task created successfully!")
                # st.json(result) # Can be too verbose
                
                # Trigger refresh of task list
                if "task_list_refresh" not in st.session_state:
                    st.session_state.task_list_refresh = 0
                st.session_state.task_list_refresh += 1

            except Exception as e:
                st.error(f"❌ Error creating task: {str(e)}")
            
            del st.session_state['create_task_future']
        else:
            # The spinner is implicitly handled by the rerun and this check
            st.spinner("Creating task...")


def render_task_examples():
    """Render example tasks for inspiration."""
    with st.expander("💡 Example Tasks"):
        examples = [
            "Take a screenshot of the desktop",
            "Open Firefox and navigate to Wikipedia",
            "Create a new text file with today's date",
        ]
        
        for example in examples:
            if st.button(f"📋 {example}", key=f"example_{example}"):
                st.session_state.example_description = example
                st.rerun()