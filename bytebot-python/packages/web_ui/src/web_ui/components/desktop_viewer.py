"""Desktop viewer component."""

import streamlit as st
import asyncio
import base64
from PIL import Image
import io
import logging

# Set up logging
logger = logging.getLogger(__name__)


def render_desktop_viewer():
    """Render the desktop viewer interface."""
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        # Control panel
        st.subheader("🎮 Controls")
        
        if st.button("📷 Take Screenshot", use_container_width=True):
            take_screenshot_and_display()
        
        if st.button("🔄 Refresh View", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        # Mouse control
        st.subheader("🖱️ Mouse Control")
        
        col_x, col_y = st.columns(2)
        with col_x:
            click_x = st.number_input("X", min_value=0, max_value=1920, value=640)
        with col_y:
            click_y = st.number_input("Y", min_value=0, max_value=1080, value=480)
        
        button_type = st.selectbox("Button", ["left", "right", "middle"])
        
        if st.button("🖱️ Click", use_container_width=True):
            click_mouse(click_x, click_y, button_type)
        
        st.markdown("---")
        
        # Keyboard control
        st.subheader("⌨️ Keyboard Control")
        
        text_input = st.text_input("Text to type:")
        if st.button("⌨️ Type Text", use_container_width=True) and text_input:
            type_text(text_input)
        
        # Quick actions
        st.markdown("**Quick Keys:**")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Enter", use_container_width=True):
                type_text("\n")
        with col_b:
            if st.button("Escape", use_container_width=True):
                # Would send escape key
                st.info("ESC key functionality")
    
    with col1:
        # Main desktop display
        st.subheader("🖥️ Virtual Desktop")
        
        # Display current screenshot if available
        if "current_screenshot" in st.session_state:
            display_desktop_screenshot()
        else:
            # Placeholder
            st.info("👆 Click 'Take Screenshot' to see the virtual desktop")
            st.image("https://via.placeholder.com/800x600/f3f4f6/6b7280?text=Virtual+Desktop+View", 
                    caption="Virtual desktop will appear here")


def take_screenshot_and_display():
    """Take a screenshot and display it."""
    try:
        with st.spinner("Taking screenshot..."):
            logger.info("Starting screenshot capture process")
            api_client = st.session_state.api_client
            result = asyncio.run(api_client.take_screenshot())
            
            logger.info(f"Screenshot API result: {result is not None}")
            if result:
                logger.info(f"Screenshot result keys: {list(result.keys())}")
                logger.info(f"Screenshot contains 'data': {'data' in result}")
                logger.info(f"Screenshot contains 'image': {'image' in result}")
                
                # Check for different possible response formats
                image_key = None
                if "data" in result:
                    image_key = "data"
                elif "image" in result:
                    image_key = "image"
                
                if image_key:
                    logger.info(f"Using image key: {image_key}")
                    logger.info(f"Image data length: {len(result[image_key])}")
                    st.session_state.current_screenshot = result
                    st.success("📷 Screenshot captured!")
                    st.rerun()
                else:
                    logger.error(f"No image data found in result. Available keys: {list(result.keys())}")
                    st.error("❌ No image data found in screenshot response.")
            else:
                logger.error("Screenshot API returned None")
                st.error("❌ Failed to take screenshot. Check if computer control service is running.")
                
    except Exception as e:
        logger.error(f"Error taking screenshot: {str(e)}", exc_info=True)
        st.error(f"❌ Error taking screenshot: {str(e)}")


def display_desktop_screenshot():
    """Display the current desktop screenshot."""
    screenshot_data = st.session_state.current_screenshot
    
    logger.info(f"Displaying screenshot with keys: {list(screenshot_data.keys())}")
    
    # Check for different possible image keys
    image_key = None
    if "data" in screenshot_data:
        image_key = "data"
    elif "image" in screenshot_data:
        image_key = "image"
    
    if image_key:
        try:
            logger.info(f"Using image key '{image_key}' with data length: {len(screenshot_data[image_key])}")
            
            # Decode base64 image
            image_data = base64.b64decode(screenshot_data[image_key])
            logger.info(f"Decoded image data length: {len(image_data)}")
            
            image = Image.open(io.BytesIO(image_data))
            logger.info(f"PIL Image size: {image.size}, mode: {image.mode}")
            
            # Display with click coordinates
            st.image(
                image, 
                caption=f"Desktop Screenshot - {screenshot_data.get('width', 'Unknown')}x{screenshot_data.get('height', 'Unknown')}",
                use_container_width=True
            )
            
            # Add click handler info
            st.info("💡 Note the coordinates when you want to click. Use the mouse controls on the right.")
            
            # Screenshot metadata
            with st.expander("📊 Screenshot Info"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Width", screenshot_data.get("width", "Unknown"))
                with col2:
                    st.metric("Height", screenshot_data.get("height", "Unknown"))
                with col3:
                    st.metric("Format", screenshot_data.get("format", "PNG"))
                    
        except Exception as e:
            logger.error(f"Error displaying screenshot: {str(e)}", exc_info=True)
            st.error(f"❌ Error displaying screenshot: {str(e)}")
    else:
        logger.error(f"No image data found. Available keys: {list(screenshot_data.keys())}")
        st.error("❌ No image data found in screenshot")


def click_mouse(x: int, y: int, button: str):
    """Click mouse at specified coordinates."""
    try:
        with st.spinner(f"Clicking at ({x}, {y})..."):
            api_client = st.session_state.api_client
            result = asyncio.run(api_client.click_mouse(x, y, button))
            
            if result:
                st.success(f"✅ Clicked {button} button at ({x}, {y})")
                # Auto-refresh screenshot after click
                st.session_state.auto_screenshot_after_action = True
            else:
                st.error("❌ Failed to click mouse")
                
    except Exception as e:
        st.error(f"❌ Error clicking mouse: {str(e)}")


def type_text(text: str):
    """Type text on the virtual desktop."""
    try:
        with st.spinner(f"Typing text..."):
            api_client = st.session_state.api_client
            result = asyncio.run(api_client.type_text(text))
            
            if result:
                st.success(f"✅ Typed: {text[:50]}{'...' if len(text) > 50 else ''}")
            else:
                st.error("❌ Failed to type text")
                
    except Exception as e:
        st.error(f"❌ Error typing text: {str(e)}")


def render_desktop_controls():
    """Render additional desktop controls."""
    with st.expander("🔧 Advanced Controls"):
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🗂️ Applications")
            apps = ["firefox", "vscode", "terminal", "desktop"]
            selected_app = st.selectbox("Launch App", apps)
            if st.button("🚀 Launch", use_container_width=True):
                launch_application(selected_app)
        
        with col2:
            st.subheader("⏱️ Timing")
            wait_time = st.slider("Wait (seconds)", 0.1, 5.0, 1.0, 0.1)
            if st.button("⏰ Wait", use_container_width=True):
                wait_action(wait_time)


def launch_application(app_name: str):
    """Launch an application."""
    try:
        with st.spinner(f"Launching {app_name}..."):
            api_client = st.session_state.api_client
            data = {"action": "application", "application": app_name}
            result = asyncio.run(api_client.post_computer("/computer-use", data))
            
            if result:
                st.success(f"✅ Launched {app_name}")
            else:
                st.error(f"❌ Failed to launch {app_name}")
                
    except Exception as e:
        st.error(f"❌ Error launching application: {str(e)}")


def wait_action(seconds: float):
    """Wait for specified time."""
    try:
        with st.spinner(f"Waiting {seconds} seconds..."):
            api_client = st.session_state.api_client
            data = {"action": "wait", "duration": int(seconds * 1000)}  # Convert to milliseconds
            result = asyncio.run(api_client.post_computer("/computer-use", data))
            
            if result:
                st.success(f"✅ Waited {seconds} seconds")
            else:
                st.error("❌ Wait action failed")
                
    except Exception as e:
        st.error(f"❌ Error with wait action: {str(e)}")