"""Live Desktop View component with Take Over functionality."""

import streamlit as st
import base64
from PIL import Image
import io
import logging
import uuid
from datetime import datetime

from ..services.input_capture_service import input_capture_service

logger = logging.getLogger(__name__)

def render_live_desktop_view():
    """Render the live desktop view interface with Take Over functionality."""
    # Initialize session state
    if "take_over_mode" not in st.session_state:
        st.session_state.take_over_mode = False
    if "input_capture_active" not in st.session_state:
        st.session_state.input_capture_active = False
    if "current_task_id" not in st.session_state:
        st.session_state.current_task_id = None
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    
    # Control Mode Toggle
    render_control_mode_toggle()
    
    # Control settings based on mode
    if st.session_state.take_over_mode:
        render_take_over_mode_settings()
    else:
        render_standard_live_view_settings()
    
    st.markdown("---")
    
    # Handle auto-refresh (but not when manual actions are pending)
    auto_refresh = st.session_state.get("live_desktop_auto_refresh", False)
    if auto_refresh:
        # Don't auto-refresh if we have pending actions to avoid interference
        has_pending_actions = (
            'live_click_future' in st.session_state or 
            'live_type_future' in st.session_state or 
            'live_app_future' in st.session_state or
            'live_screenshot_future' in st.session_state or  # Also check for pending screenshot
            st.session_state.get('live_refresh_after_action', False)
        )
        
        if not has_pending_actions:
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
    # Don't call st.rerun() immediately - let the natural page flow handle it


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
            # Only rerun once when the screenshot completes
            st.rerun()
        else:
            # Don't use st.spinner() as it causes continuous reruns
            # Show status and schedule a rerun after a delay to check again
            st.info("🔄 Taking screenshot...")
            
            # Use a simple timeout approach - rerun after 1 second to check again
            import time
            import threading
            
            def check_future_later():
                time.sleep(1.0)  # Wait 1 second
                try:
                    # Only rerun if the future still exists and might be done
                    if 'live_screenshot_future' in st.session_state:
                        st.rerun()
                except:
                    pass  # Ignore rerun errors
                    
            # Start the delayed check in background
            threading.Thread(target=check_future_later, daemon=True).start()


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
    
    # Disable auto-refresh when user takes manual action
    st.session_state.live_desktop_auto_refresh = False
    
    # First click
    click_future = runner.run(api_client.click_mouse(x, y, button))
    st.session_state['live_click_future'] = (f"Click at ({x}, {y})", click_future)
    
    # Record as user action if in Take Over mode and input capture is active
    if (st.session_state.get('take_over_mode', False) and 
        st.session_state.get('input_capture_active', False) and 
        st.session_state.get('current_task_id')):
        
        # Get current screenshot for context
        screenshot_data = None
        if "live_current_screenshot" in st.session_state:
            screenshot_data = st.session_state.live_current_screenshot.get("data") or st.session_state.live_current_screenshot.get("image")
        
        input_capture_service.capture_click_action(
            x=x, y=y, button=button, click_count=1, screenshot_data=screenshot_data
        )
    
    # Set flag to refresh after click (but don't rerun immediately)
    st.session_state['live_refresh_after_action'] = True
    # Removed st.rerun() to prevent immediate loop


def trigger_live_type_and_refresh(text: str):
    """Trigger text typing and then refresh desktop.""" 
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    # Disable auto-refresh when user takes manual action
    st.session_state.live_desktop_auto_refresh = False
    
    # First type
    type_future = runner.run(api_client.type_text(text))
    st.session_state['live_type_future'] = (f"Type: {text[:20]}...", type_future)
    
    # Record as user action if in Take Over mode and input capture is active
    if (st.session_state.get('take_over_mode', False) and 
        st.session_state.get('input_capture_active', False) and 
        st.session_state.get('current_task_id')):
        
        # Get current screenshot for context
        screenshot_data = None
        if "live_current_screenshot" in st.session_state:
            screenshot_data = st.session_state.live_current_screenshot.get("data") or st.session_state.live_current_screenshot.get("image")
        
        input_capture_service.capture_type_text_action(
            text=text, screenshot_data=screenshot_data
        )
    
    # Set flag to refresh after typing (but don't rerun immediately)
    st.session_state['live_refresh_after_action'] = True
    # Removed st.rerun() to prevent immediate loop


def trigger_live_open_application(app: str):
    """Open an application and refresh desktop."""
    api_client = st.session_state.api_client
    runner = st.session_state.async_runner
    
    # Disable auto-refresh when user takes manual action
    st.session_state.live_desktop_auto_refresh = False
    
    # Launch application
    app_future = runner.run(api_client.post_computer("/computer-use", {
        "action": "application", 
        "application": app
    }))
    st.session_state['live_app_future'] = (f"Launch {app}", app_future)
    
    # Set flag to refresh after app launch (but don't rerun immediately)
    st.session_state['live_refresh_after_action'] = True
    # Removed st.rerun() to prevent immediate loop


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


def render_control_mode_toggle():
    """Render the control mode toggle."""
    st.markdown("### 🎮 Control Mode")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖥️ Live View Mode", 
                    disabled=not st.session_state.take_over_mode,
                    use_container_width=True):
            st.session_state.take_over_mode = False
            st.session_state.input_capture_active = False
            if input_capture_service.is_capturing():
                input_capture_service.stop_capture()
            st.rerun()
    
    with col2:
        if st.button("🎮 Take Over Mode", 
                    disabled=st.session_state.take_over_mode,
                    use_container_width=True):
            st.session_state.take_over_mode = True
            st.rerun()


def render_standard_live_view_settings():
    """Render standard live view settings."""
    st.markdown("#### 🖥️ Standard Live View")
    
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
            # Disable auto-refresh when user manually refreshes
            st.session_state.live_desktop_auto_refresh = False
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


def render_take_over_mode_settings():
    """Render Take Over mode settings."""
    st.markdown("#### 🎮 Take Over Mode")
    
    # Task selection
    render_task_selection_for_takeover()
    
    # Input capture controls
    render_input_capture_controls_in_live_view()
    
    # Manual refresh in take over mode
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📷 Take Screenshot", use_container_width=True):
            trigger_live_screenshot()
    with col2:
        if st.button("🔄 Refresh View", use_container_width=True):
            st.rerun()


def render_task_selection_for_takeover():
    """Render task selection for Take Over mode in live view."""
    if not st.session_state.tasks:
        # Try to load tasks
        if hasattr(st.session_state, 'api_client'):
            try:
                api_client = st.session_state.api_client
                runner = st.session_state.async_runner
                # This would need to be async, but for now just show info
                st.info("🔍 Load tasks from the Tasks & Desktop section first to enable Take Over mode.")
                return
            except:
                pass
    
    running_tasks = [task for task in st.session_state.tasks if task.get("status") == "RUNNING"]
    
    if not running_tasks:
        st.info("🔍 No running tasks found. Start a task first to take over.")
        return
    
    st.markdown("##### Select Running Task to Take Over")
    
    task_options = {f"{task['description'][:50]}... (ID: {task['id'][:8]})": task['id'] 
                   for task in running_tasks}
    
    selected_task_key = st.selectbox(
        "Choose a running task:",
        list(task_options.keys()),
        key="live_task_selector"
    )
    
    if selected_task_key:
        selected_task_id = task_options[selected_task_key]
        st.session_state.current_task_id = selected_task_id
        st.success(f"✅ Selected task: {selected_task_id[:8]}...")


def render_input_capture_controls_in_live_view():
    """Render input capture controls in live view."""
    if not st.session_state.current_task_id:
        return
    
    st.markdown("##### 📹 Input Capture")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔴 Start Capture" if not st.session_state.input_capture_active else "⏹️ Stop Capture",
                    use_container_width=True):
            st.session_state.input_capture_active = not st.session_state.input_capture_active
            if st.session_state.input_capture_active:
                start_input_capture_live()
            else:
                stop_input_capture_live()
            st.rerun()
    
    with col2:
        if st.session_state.input_capture_active:
            st.success("🟢 Capturing input...")
        else:
            st.info("⚪ Input capture stopped")
    
    if st.session_state.input_capture_active:
        st.info("💡 **Tip**: Your actions will be captured and can be sent to the AI agent.")
    
    # Display captured actions summary
    if input_capture_service.is_capturing() or input_capture_service.get_captured_actions():
        render_captured_actions_summary_live()


def start_input_capture_live():
    """Start input capture in live view."""
    if not st.session_state.current_task_id:
        return
    
    try:
        success = input_capture_service.start_capture(st.session_state.current_task_id)
        if success:
            logger.info(f"Started input capture for task {st.session_state.current_task_id}")
            st.success("🔴 Input capture started")
        else:
            st.error("❌ Failed to start input capture")
            st.session_state.input_capture_active = False
    except Exception as e:
        st.error(f"❌ Failed to start input capture: {e}")
        st.session_state.input_capture_active = False


def stop_input_capture_live():
    """Stop input capture in live view."""
    try:
        success = input_capture_service.stop_capture()
        if success:
            logger.info("Stopped input capture")
            st.success("⏹️ Input capture stopped")
        else:
            st.warning("⚠️ Input capture was not active")
    except Exception as e:
        st.error(f"❌ Failed to stop input capture: {e}")


def render_captured_actions_summary_live():
    """Render captured actions summary in live view."""
    captured_actions = input_capture_service.get_captured_actions()
    
    if not captured_actions:
        return
    
    st.markdown("##### 📝 Captured Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Actions", len(captured_actions))
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            input_capture_service.clear_captured_actions()
            st.rerun()
    with col3:
        if st.button("🚀 Send to AI", use_container_width=True, type="primary"):
            send_captured_actions_live()
    
    # Show recent actions
    if st.expander(f"View {len(captured_actions)} actions", expanded=False):
        for action in reversed(captured_actions[-5:]):  # Show last 5
            timestamp = datetime.fromisoformat(action["timestamp"])
            action_type = action["action_type"].replace("_", " ").title()
            st.text(f"{timestamp.strftime('%H:%M:%S')} - {action_type}")


def send_captured_actions_live():
    """Send captured actions from live view."""
    try:
        api_client = st.session_state.api_client
        success = input_capture_service.send_captured_actions_to_task(api_client)
        
        if success:
            st.success("✅ Actions sent to AI agent!")
            input_capture_service.clear_captured_actions()
        else:
            st.error("❌ Failed to send actions to AI")
            
    except Exception as e:
        st.error(f"❌ Error sending actions: {e}")
    
    st.rerun()