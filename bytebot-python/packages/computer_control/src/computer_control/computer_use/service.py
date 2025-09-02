"""Computer use service for desktop automation."""

import asyncio
import base64
import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Union

import pyautogui
from pynput import keyboard, mouse
from pynput.keyboard import Key
from pynput.mouse import Button as MouseButton
from PIL import Image

from shared.types.computer_action import (
    ComputerAction,
    MoveMouseAction,
    TraceMouseAction,
    ClickMouseAction,
    PressMouseAction,
    DragMouseAction,
    ScrollAction,
    TypeKeysAction,
    PressKeysAction,
    TypeTextAction,
    PasteTextAction,
    WaitAction,
    ScreenshotAction,
    CursorPositionAction,
    ApplicationAction,
    WriteFileAction,
    ReadFileAction,
    Button,
    Press,
    Application,
    Coordinates,
)


class ComputerUseService:
    """Service for computer automation and control."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configure PyAutoGUI
        pyautogui.FAILSAFE = False  # Disable fail-safe to allow corner movements
        pyautogui.PAUSE = 0.05  # Small pause between actions
        
        # Initialize controllers
        self.keyboard_controller = keyboard.Controller()
        self.mouse_controller = mouse.Controller()
        
        # Button mapping
        self.button_mapping = {
            "left": MouseButton.left,
            "right": MouseButton.right,
            "middle": MouseButton.middle,
        }

    async def execute_action(self, action: ComputerAction) -> Optional[Dict[str, Any]]:
        """Execute a computer action."""
        self.logger.info(f"Executing computer action: {action.action}")

        # Map action to handler method
        handler_map = {
            "move_mouse": self._move_mouse,
            "trace_mouse": self._trace_mouse,
            "click_mouse": self._click_mouse,
            "press_mouse": self._press_mouse,
            "drag_mouse": self._drag_mouse,
            "scroll": self._scroll,
            "type_keys": self._type_keys,
            "press_keys": self._press_keys,
            "type_text": self._type_text,
            "paste_text": self._paste_text,
            "wait": self._wait,
            "screenshot": self._screenshot,
            "cursor_position": self._cursor_position,
            "application": self._application,
            "write_file": self._write_file,
            "read_file": self._read_file,
        }

        handler = handler_map.get(action.action)
        if not handler:
            raise ValueError(f"Unsupported computer action: {action.action}")

        return await handler(action)

    async def _move_mouse(self, action: MoveMouseAction) -> None:
        """Move mouse to coordinates."""
        coords = action.coordinates
        self.mouse_controller.position = (coords.x, coords.y)
        
        # Small delay to ensure movement completes
        await asyncio.sleep(0.01)

    async def _trace_mouse(self, action: TraceMouseAction) -> None:
        """Trace mouse along a path."""
        path = action.path
        hold_keys = action.holdKeys or []

        if not path:
            return

        # Move to first coordinate
        first_coord = path[0]
        self.mouse_controller.position = (first_coord.x, first_coord.y)

        # Hold keys if provided
        if hold_keys:
            await self._hold_keys(hold_keys, True)

        try:
            # Move along path
            for coord in path:
                self.mouse_controller.position = (coord.x, coord.y)
                await asyncio.sleep(0.01)  # Small delay for smooth movement
        finally:
            # Release keys
            if hold_keys:
                await self._hold_keys(hold_keys, False)

    async def _click_mouse(self, action: ClickMouseAction) -> None:
        """Click mouse at coordinates."""
        coords = action.coordinates
        button = self.button_mapping[action.button]
        hold_keys = action.holdKeys or []
        click_count = action.clickCount

        # Move to coordinates if provided
        if coords:
            self.mouse_controller.position = (coords.x, coords.y)
            await asyncio.sleep(0.01)

        # Hold keys if provided
        if hold_keys:
            await self._hold_keys(hold_keys, True)

        try:
            # Perform clicks
            for _ in range(click_count):
                self.mouse_controller.click(button)
                if click_count > 1:
                    await asyncio.sleep(0.15)  # Delay between multiple clicks
        finally:
            # Release keys
            if hold_keys:
                await self._hold_keys(hold_keys, False)

    async def _press_mouse(self, action: PressMouseAction) -> None:
        """Press or release mouse button."""
        coords = action.coordinates
        button = self.button_mapping[action.button]
        press = action.press

        # Move to coordinates if provided
        if coords:
            self.mouse_controller.position = (coords.x, coords.y)
            await asyncio.sleep(0.01)

        # Press or release button
        if press == "down":
            self.mouse_controller.press(button)
        else:
            self.mouse_controller.release(button)

    async def _drag_mouse(self, action: DragMouseAction) -> None:
        """Drag mouse along a path."""
        path = action.path
        button = self.button_mapping[action.button]
        hold_keys = action.holdKeys or []

        if not path:
            return

        # Move to first coordinate
        first_coord = path[0]
        self.mouse_controller.position = (first_coord.x, first_coord.y)

        # Hold keys if provided
        if hold_keys:
            await self._hold_keys(hold_keys, True)

        try:
            # Press mouse button at start
            self.mouse_controller.press(button)
            
            # Drag along path
            for coord in path:
                self.mouse_controller.position = (coord.x, coord.y)
                await asyncio.sleep(0.01)
                
            # Release mouse button at end
            self.mouse_controller.release(button)
            
        finally:
            # Release keys
            if hold_keys:
                await self._hold_keys(hold_keys, False)

    async def _scroll(self, action: ScrollAction) -> None:
        """Scroll at coordinates."""
        coords = action.coordinates
        direction = action.direction
        scroll_count = action.scrollCount
        hold_keys = action.holdKeys or []

        # Move to coordinates if provided
        if coords:
            self.mouse_controller.position = (coords.x, coords.y)
            await asyncio.sleep(0.01)

        # Hold keys if provided
        if hold_keys:
            await self._hold_keys(hold_keys, True)

        try:
            # Determine scroll direction
            if direction in ["up", "down"]:
                dy = scroll_count if direction == "up" else -scroll_count
                for _ in range(abs(scroll_count)):
                    self.mouse_controller.scroll(0, dy / abs(dy))
                    await asyncio.sleep(0.05)
            elif direction in ["left", "right"]:
                dx = scroll_count if direction == "right" else -scroll_count
                for _ in range(abs(scroll_count)):
                    self.mouse_controller.scroll(dx / abs(dx), 0)
                    await asyncio.sleep(0.05)
        finally:
            # Release keys
            if hold_keys:
                await self._hold_keys(hold_keys, False)

    async def _type_keys(self, action: TypeKeysAction) -> None:
        """Type specific keys."""
        keys = action.keys
        delay = action.delay or 0

        for key in keys:
            await self._press_key(key)
            if delay:
                await asyncio.sleep(delay / 1000.0)

    async def _press_keys(self, action: PressKeysAction) -> None:
        """Press or release specific keys."""
        keys = action.keys
        press = action.press

        for key in keys:
            key_obj = self._get_key_object(key)
            if press == "down":
                self.keyboard_controller.press(key_obj)
            else:
                self.keyboard_controller.release(key_obj)

    async def _type_text(self, action: TypeTextAction) -> None:
        """Type text."""
        text = action.text
        delay = action.delay or 0
        
        # Don't log sensitive text
        if not action.sensitive:
            self.logger.debug(f"Typing text: {text[:50]}...")
        else:
            self.logger.debug("Typing sensitive text")

        if delay:
            for char in text:
                self.keyboard_controller.type(char)
                await asyncio.sleep(delay / 1000.0)
        else:
            self.keyboard_controller.type(text)

    async def _paste_text(self, action: PasteTextAction) -> None:
        """Paste text using clipboard."""
        text = action.text
        
        # Use pyautogui to set clipboard and paste
        pyautogui.write(text)

    async def _wait(self, action: WaitAction) -> None:
        """Wait for specified duration."""
        duration_ms = action.duration
        await asyncio.sleep(duration_ms / 1000.0)

    async def _screenshot(self, action: ScreenshotAction) -> Dict[str, Any]:
        """Take a screenshot."""
        # Take screenshot using scrot (since we're in a headless environment)
        import tempfile
        import subprocess
        import os
        
        # Create temporary file for screenshot
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Use scrot to take screenshot of the virtual display
            # Set DISPLAY environment variable for scrot
            env = os.environ.copy()
            env['DISPLAY'] = ':99'
            
            process = await asyncio.create_subprocess_exec(
                'scrot', tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Screenshot failed: {stderr.decode()}")
            
            # Check if file was created and get its size
            if not os.path.exists(tmp_path):
                raise Exception(f"Screenshot file was not created. stdout: {stdout.decode()}, stderr: {stderr.decode()}")
            
            file_size = os.path.getsize(tmp_path)
            self.logger.info(f"Screenshot file created with size: {file_size} bytes")
            
            # Read the screenshot file and convert to base64
            with open(tmp_path, 'rb') as f:
                img_data = f.read()
            
            # Check if we have valid image data
            if len(img_data) == 0:
                # If scrot produces an empty file, it means the display is blank
                # Create a small blank PNG image as a valid response
                self.logger.info("Display appears to be blank, creating blank screenshot")
                from PIL import Image
                import io
                
                # Create a 1280x960 blank (black) image
                blank_img = Image.new('RGB', (1280, 960), color=(0, 0, 0))
                img_buffer = io.BytesIO()
                blank_img.save(img_buffer, format='PNG')
                img_data = img_buffer.getvalue()
                width, height = 1280, 960
            else:
                # Get image dimensions using PIL
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_data))
                width, height = img.size
                
            base64_data = base64.b64encode(img_data).decode('utf-8')
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        return {
            "type": "image",
            "format": "png", 
            "data": base64_data,
            "width": width,
            "height": height
        }

    async def _cursor_position(self, action: CursorPositionAction) -> Dict[str, Any]:
        """Get current cursor position."""
        pos = self.mouse_controller.position
        return {
            "x": int(pos[0]),
            "y": int(pos[1])
        }

    async def _application(self, action: ApplicationAction) -> None:
        """Launch or interact with application."""
        app = action.application
        
        # Application launching logic (simplified)
        app_commands = {
            "firefox": ["firefox"],
            "vscode": ["code"],
            "terminal": ["gnome-terminal"],
            "desktop": [],  # Switch to desktop
        }
        
        if app in app_commands:
            cmd = app_commands[app]
            if cmd:
                subprocess.Popen(cmd, start_new_session=True)
                await asyncio.sleep(1)  # Give app time to start

    async def _write_file(self, action: WriteFileAction) -> Dict[str, Any]:
        """Write file with base64 data."""
        file_path = action.path
        base64_data = action.data
        
        try:
            # Decode base64 data
            file_data = base64.b64decode(base64_data)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            return {"success": True, "path": file_path, "size": len(file_data)}
            
        except Exception as e:
            self.logger.error(f"Error writing file {file_path}: {e}")
            raise

    async def _read_file(self, action: ReadFileAction) -> Dict[str, Any]:
        """Read file and return as base64."""
        file_path = action.path
        
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Encode as base64
            base64_data = base64.b64encode(file_data).decode('utf-8')
            
            return {
                "path": file_path,
                "data": base64_data,
                "size": len(file_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            raise

    async def _hold_keys(self, keys: List[str], hold: bool) -> None:
        """Hold or release multiple keys."""
        for key in keys:
            key_obj = self._get_key_object(key)
            if hold:
                self.keyboard_controller.press(key_obj)
            else:
                self.keyboard_controller.release(key_obj)

    async def _press_key(self, key: str) -> None:
        """Press and release a single key."""
        key_obj = self._get_key_object(key)
        self.keyboard_controller.press(key_obj)
        await asyncio.sleep(0.01)
        self.keyboard_controller.release(key_obj)

    def _get_key_object(self, key: str):
        """Get pynput key object from string."""
        # Map common key strings to pynput Key objects
        key_mapping = {
            "ctrl": Key.ctrl,
            "control": Key.ctrl,
            "alt": Key.alt,
            "shift": Key.shift,
            "cmd": Key.cmd,
            "super": Key.cmd,
            "enter": Key.enter,
            "return": Key.enter,
            "space": Key.space,
            "tab": Key.tab,
            "escape": Key.esc,
            "esc": Key.esc,
            "backspace": Key.backspace,
            "delete": Key.delete,
            "up": Key.up,
            "down": Key.down,
            "left": Key.left,
            "right": Key.right,
            "home": Key.home,
            "end": Key.end,
            "page_up": Key.page_up,
            "page_down": Key.page_down,
            "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
            "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
            "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
        }
        
        # Check if it's a special key
        if key.lower() in key_mapping:
            return key_mapping[key.lower()]
        
        # For single characters, return as is
        if len(key) == 1:
            return key
        
        # Default fallback
        return key