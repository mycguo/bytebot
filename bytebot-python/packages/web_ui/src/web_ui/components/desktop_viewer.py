"""Desktop viewer component."""

import streamlit as st
import base64
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def render_desktop_viewer():
    """Render the desktop viewer interface."""
    col1, col2 = st.columns([3, 1])
    
    with col2:
        render_controls()
    
    with col1:
        st.subheader("🖥️ Virtual Desktop")
        render_screenshot_result() # Handles showing spinner or result
        display_desktop_screenshot() # Displays the actual image if available


def render_controls():
    """Render the control panel for the desktop viewer."""
    st.subheader("🎮 Controls")
    
    if st.button("📷 Take Screenshot", use_container_width=True):
        trigger_screenshot()
    
    if st.button("🔄 Refresh View", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    st.subheader("🖱️ Mouse Control")
    col_x, col_y = st.columns(2)
    with col_x:
        click_x = st.number_input("X", 0, 1920, 640)
    with col_y:
        click_y = st.number_input("Y", 0, 1080, 480)
    button_type = st.selectbox("Button", ["left", "right", "middle"])
    if st.button("🖱️ Click", use_container_width=True):
        trigger_click_mouse(click_x, click_y, button_type)
    
    st.markdown("---")
    
    st.subheader("⌨️ Keyboard Control")
    text_input = st.text_input("Text to type:")
    if st.button("⌨️ Type Text", use_container_width=True) and text_input:
        trigger_type_text(text_input)

    render_control_action_results()


def trigger_screenshot():
    """Triggers an asynchronous screenshot capture."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    future = runner.run(api_client.take_screenshot())
    st.session_state['screenshot_future'] = future
    st.rerun()


def render_screenshot_result():
    """Renders the result of the screenshot future."""
    if 'screenshot_future' in st.session_state:
        future = st.session_state['screenshot_future']
        if future.done():
            try:
                result = future.result()
                if result and ("data" in result or "image" in result):
                    st.session_state.current_screenshot = result
                    st.success("📷 Screenshot captured!")
                else:
                    st.error("❌ Failed to get screenshot data.")
            except Exception as e:
                st.error(f"❌ Error taking screenshot: {e}")
            del st.session_state['screenshot_future']
        else:
            st.spinner("Taking screenshot...")


def display_desktop_screenshot():
    """Displays the current desktop screenshot from session state."""
    if "current_screenshot" in st.session_state:
        screenshot_data = st.session_state.current_screenshot
        image_key = "data" if "data" in screenshot_data else "image"
        try:
            image_data = base64.b64decode(screenshot_data[image_key])
            image = Image.open(io.BytesIO(image_data))
            st.image(image, caption="Desktop Screenshot", use_container_width=True)
        except Exception as e:
            st.error(f"❌ Error displaying screenshot: {e}")
    else:
        st.info("👆 Click 'Take Screenshot' to see the virtual desktop")


def trigger_click_mouse(x: int, y: int, button: str):
    """Triggers an asynchronous mouse click."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    future = runner.run(api_client.click_mouse(x, y, button))
    st.session_state['control_action_future'] = (f"Click at ({x}, {y})", future)
    st.rerun()


def trigger_type_text(text: str):
    """Triggers asynchronous text typing."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    future = runner.run(api_client.type_text(text))
    st.session_state['control_action_future'] = (f"Type: {text[:20]}...", future)
    st.rerun()


def render_control_action_results():
    """Renders the status of the latest control action future."""
    if 'control_action_future' in st.session_state:
        action_name, future = st.session_state['control_action_future']
        if future.done():
            try:
                future.result()
                st.success(f"✅ Action successful: {action_name}")
                # Trigger a new screenshot to see the result
                trigger_screenshot()
            except Exception as e:
                st.error(f"❌ Error during '{action_name}': {e}")
            del st.session_state['control_action_future']
        else:
            st.spinner(f"Performing action: {action_name}...")