"""Live Desktop View component - similar to TypeScript implementation."""

import streamlit as st
import base64
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def render_live_desktop_view():
    """Render the live desktop view interface - showing desktop in full width."""
    # Auto-refresh toggle
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        auto_refresh = st.checkbox(
            "🔄 Auto Refresh", 
            value=st.session_state.get("live_desktop_auto_refresh", False),
            help="Automatically refresh the desktop view every few seconds"
        )
        st.session_state.live_desktop_auto_refresh = auto_refresh
    
    with col2:
        if st.button("📷 Refresh Now", use_container_width=True):
            trigger_live_screenshot()
    
    with col3:
        refresh_interval = st.slider(
            "Refresh Interval (seconds)",
            min_value=1,
            max_value=10,
            value=st.session_state.get("live_refresh_interval", 3),
            help="How often to auto-refresh the desktop"
        )
        st.session_state.live_refresh_interval = refresh_interval
    
    st.markdown("---")
    
    # Handle auto-refresh
    if auto_refresh:
        if "last_live_refresh" not in st.session_state:
            st.session_state.last_live_refresh = 0
        
        import time
        current_time = time.time()
        if current_time - st.session_state.last_live_refresh > refresh_interval:
            trigger_live_screenshot()
            st.session_state.last_live_refresh = current_time
    
    # Handle screenshot results
    render_live_screenshot_result()
    
    # Display the live desktop
    display_live_desktop()
    
    # Control panel at the bottom
    render_live_desktop_controls()


def trigger_live_screenshot():
    """Trigger a screenshot for live desktop view."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    future = runner.run(api_client.take_screenshot())
    st.session_state['live_screenshot_future'] = future
    st.rerun()


def render_live_screenshot_result():
    """Handle the result of live screenshot future."""
    if 'live_screenshot_future' in st.session_state:
        future = st.session_state['live_screenshot_future']
        if future.done():
            try:
                result = future.result()
                if result and ("data" in result or "image" in result):
                    st.session_state.live_current_screenshot = result
                    # Auto-refresh timestamp
                    import time
                    st.session_state.last_screenshot_time = time.time()
                else:
                    st.error("❌ Failed to get live desktop data.")
            except Exception as e:
                st.error(f"❌ Error capturing live desktop: {e}")
                logger.error(f"Live screenshot error: {e}")
            del st.session_state['live_screenshot_future']
        else:
            st.spinner("🔄 Capturing live desktop...")


def display_live_desktop():
    """Display the live desktop screenshot in full width."""
    if "live_current_screenshot" in st.session_state:
        screenshot_data = st.session_state.live_current_screenshot
        image_key = "data" if "data" in screenshot_data else "image"
        
        try:
            image_data = base64.b64decode(screenshot_data[image_key])
            image = Image.open(io.BytesIO(image_data))
            
            # Show timestamp if available
            if "last_screenshot_time" in st.session_state:
                import datetime
                timestamp = datetime.datetime.fromtimestamp(st.session_state.last_screenshot_time)
                st.caption(f"Last updated: {timestamp.strftime('%H:%M:%S')}")
            
            # Display the image in full width with border
            st.markdown("""
            <style>
            .live-desktop-container {
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px;
                background: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            </style>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div class="live-desktop-container">', unsafe_allow_html=True)
                st.image(
                    image, 
                    caption="🖥️ Live Desktop View", 
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"❌ Error displaying live desktop: {e}")
            logger.error(f"Display error: {e}")
    else:
        # Initial state - take first screenshot automatically
        st.info("🖥️ **Live Desktop View** - Capturing initial desktop view...")
        trigger_live_desktop_initial()


def trigger_live_desktop_initial():
    """Trigger initial screenshot when page loads."""
    if "live_desktop_initialized" not in st.session_state:
        st.session_state.live_desktop_initialized = True
        trigger_live_screenshot()


def render_live_desktop_controls():
    """Render control panel for live desktop interactions."""
    st.markdown("---")
    st.subheader("🎮 Live Desktop Controls")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Mouse control
        with st.expander("🖱️ Mouse Control", expanded=False):
            subcol1, subcol2, subcol3 = st.columns(3)
            with subcol1:
                click_x = st.number_input("X", 0, 1280, 640, key="live_mouse_x")
            with subcol2:
                click_y = st.number_input("Y", 0, 960, 480, key="live_mouse_y")
            with subcol3:
                button_type = st.selectbox("Button", ["left", "right", "middle"], key="live_mouse_button")
            
            if st.button("🖱️ Click & Refresh", use_container_width=True):
                trigger_live_click_and_refresh(click_x, click_y, button_type)
        
        # Keyboard control
        with st.expander("⌨️ Keyboard Control", expanded=False):
            text_input = st.text_input("Text to type:", key="live_keyboard_input")
            if st.button("⌨️ Type & Refresh", use_container_width=True) and text_input:
                trigger_live_type_and_refresh(text_input)
    
    with col2:
        # Quick applications
        st.markdown("**🚀 Quick Launch**")
        if st.button("🌐 Open Browser", use_container_width=True):
            trigger_live_open_application("firefox")
        if st.button("📂 File Manager", use_container_width=True):
            trigger_live_open_application("nautilus")
        if st.button("⏰ Clock", use_container_width=True):
            trigger_live_open_application("xclock")


def trigger_live_click_and_refresh(x: int, y: int, button: str):
    """Trigger mouse click and then refresh desktop."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    # First click
    click_future = runner.run(api_client.click_mouse(x, y, button))
    st.session_state['live_click_future'] = (f"Click at ({x}, {y})", click_future)
    
    # Set flag to refresh after click
    st.session_state['live_refresh_after_action'] = True
    st.rerun()


def trigger_live_type_and_refresh(text: str):
    """Trigger text typing and then refresh desktop.""" 
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    # First type
    type_future = runner.run(api_client.type_text(text))
    st.session_state['live_type_future'] = (f"Type: {text[:20]}...", type_future)
    
    # Set flag to refresh after typing
    st.session_state['live_refresh_after_action'] = True
    st.rerun()


def trigger_live_open_application(app: str):
    """Open an application and refresh desktop."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    # Launch application
    app_future = runner.run(api_client.post_computer("/computer-use", {
        "action": "application", 
        "application": app
    }))
    st.session_state['live_app_future'] = (f"Launch {app}", app_future)
    
    # Set flag to refresh after app launch
    st.session_state['live_refresh_after_action'] = True
    st.rerun()


def handle_live_action_results():
    """Handle results from live desktop actions."""
    # Handle click results
    if 'live_click_future' in st.session_state:
        action_name, future = st.session_state['live_click_future']
        if future.done():
            try:
                future.result()
                st.success(f"✅ {action_name}")
                if st.session_state.get('live_refresh_after_action'):
                    trigger_live_screenshot()
                    st.session_state['live_refresh_after_action'] = False
            except Exception as e:
                st.error(f"❌ Error: {action_name} - {e}")
            del st.session_state['live_click_future']
    
    # Handle typing results
    if 'live_type_future' in st.session_state:
        action_name, future = st.session_state['live_type_future']
        if future.done():
            try:
                future.result()
                st.success(f"✅ {action_name}")
                if st.session_state.get('live_refresh_after_action'):
                    trigger_live_screenshot()
                    st.session_state['live_refresh_after_action'] = False
            except Exception as e:
                st.error(f"❌ Error: {action_name} - {e}")
            del st.session_state['live_type_future']
    
    # Handle app launch results
    if 'live_app_future' in st.session_state:
        action_name, future = st.session_state['live_app_future']
        if future.done():
            try:
                future.result()
                st.success(f"✅ {action_name}")
                if st.session_state.get('live_refresh_after_action'):
                    # Give app time to launch before screenshot
                    import time
                    time.sleep(1)
                    trigger_live_screenshot()
                    st.session_state['live_refresh_after_action'] = False
            except Exception as e:
                st.error(f"❌ Error: {action_name} - {e}")
            del st.session_state['live_app_future']