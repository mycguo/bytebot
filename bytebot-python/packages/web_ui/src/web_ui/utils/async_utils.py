"""
Utility for running asyncio functions in a separate thread to avoid blocking the main Streamlit thread.
"""

import asyncio
import atexit
import weakref
import time
from threading import Thread, Lock
from concurrent.futures import Future, TimeoutError
from typing import Coroutine, Callable, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AsyncRunnerError(Exception):
    """Base exception for AsyncRunner errors."""
    pass


class AsyncRunnerShutdownError(AsyncRunnerError):
    """Raised when trying to use a shut down AsyncRunner."""
    pass


class AsyncRunnerInitializationError(AsyncRunnerError):
    """Raised when AsyncRunner fails to initialize."""
    pass

class AsyncRunner:
    """
    A class to run asyncio coroutines in a separate thread with proper cleanup and error handling.
    """
    _instances = weakref.WeakSet()
    _initialization_lock = Lock()
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 0.5):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[Thread] = None
        self._shutdown = False
        self._initialization_failed = False
        self._fallback_mode = False
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'initialization_attempts': 0
        }
        
        with AsyncRunner._initialization_lock:
            self._initialize()
        
        # Register for cleanup
        AsyncRunner._instances.add(self)
    
    def _initialize(self):
        """Initialize the event loop and thread with retry logic."""
        if self._shutdown:
            raise AsyncRunnerShutdownError("AsyncRunner has been shut down")
        
        if self._initialization_failed:
            raise AsyncRunnerInitializationError("AsyncRunner initialization previously failed")
        
        for attempt in range(self._max_retries):
            self._stats['initialization_attempts'] += 1
            try:
                logger.debug(f"Initializing AsyncRunner (attempt {attempt + 1}/{self._max_retries})")
                
                # Try thread-based approach first
                try:
                    self._loop = asyncio.new_event_loop()
                    self._thread = Thread(target=self._run_event_loop, daemon=True, 
                                        name=f"AsyncRunner-{id(self)}")
                    self._thread.start()
                    
                    # Verify thread started successfully
                    time.sleep(0.1)  # Give thread time to start
                    if not self._thread.is_alive():
                        raise RuntimeError("Thread failed to start")
                    
                    logger.debug(f"AsyncRunner initialized with thread successfully on attempt {attempt + 1}")
                    return
                    
                except Exception as thread_error:
                    logger.warning(f"Thread-based initialization failed: {thread_error}")
                    # Fall back to sync mode for Streamlit compatibility
                    logger.info("Falling back to synchronous mode for Streamlit compatibility")
                    
                    self._loop = None
                    self._thread = None
                    self._fallback_mode = True
                    
                    logger.debug(f"AsyncRunner initialized in fallback mode on attempt {attempt + 1}")
                    return
                
            except Exception as e:
                logger.error(f"AsyncRunner initialization attempt {attempt + 1} failed: {e}")
                
                # Clean up partial initialization
                if self._thread and self._thread.is_alive():
                    try:
                        if self._loop:
                            self._loop.call_soon_threadsafe(self._loop.stop)
                        self._thread.join(timeout=1.0)
                    except Exception as cleanup_error:
                        logger.error(f"Error during initialization cleanup: {cleanup_error}")
                
                self._loop = None
                self._thread = None
                
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                else:
                    # Final fallback - use sync mode
                    logger.warning("All initialization attempts failed, using fallback mode")
                    self._fallback_mode = True
                    return
    
    def _run_event_loop(self):
        """Run the event loop in the background thread with comprehensive error handling."""
        thread_name = threading.current_thread().name
        logger.debug(f"Starting event loop in thread {thread_name}")
        
        try:
            asyncio.set_event_loop(self._loop)
            
            # Set up exception handler for unhandled task exceptions
            def handle_exception(loop, context):
                exception = context.get('exception')
                if exception:
                    logger.error(f"Unhandled exception in async task: {exception}", exc_info=exception)
                    self._stats['tasks_failed'] += 1
                else:
                    logger.error(f"Async task error: {context['message']}")
            
            self._loop.set_exception_handler(handle_exception)
            
            logger.debug(f"Event loop running in thread {thread_name}")
            self._loop.run_forever()
            
        except Exception as e:
            logger.error(f"Critical event loop error in thread {thread_name}: {e}", exc_info=True)
            
        finally:
            logger.debug(f"Event loop cleanup starting in thread {thread_name}")
            self._cleanup_event_loop()
    
    def _cleanup_event_loop(self):
        """Clean up the event loop and cancel pending tasks."""
        if not self._loop:
            return
            
        try:
            # Get all pending tasks
            pending = asyncio.all_tasks(self._loop)
            if pending:
                logger.debug(f"Cancelling {len(pending)} pending tasks")
                
                # Cancel all pending tasks
                for task in pending:
                    if not task.done():
                        task.cancel()
                        
                # Wait for cancelled tasks to complete with timeout
                try:
                    self._loop.run_until_complete(
                        asyncio.wait_for(
                            asyncio.gather(*pending, return_exceptions=True),
                            timeout=3.0
                        )
                    )
                except TimeoutError:
                    logger.warning("Timeout waiting for tasks to cancel")
                except Exception as e:
                    logger.error(f"Error waiting for task cancellation: {e}")
                    
        except Exception as e:
            logger.error(f"Error during task cleanup: {e}")
            
        finally:
            try:
                # Close the loop
                if not self._loop.is_closed():
                    self._loop.close()
                    logger.debug("Event loop closed")
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")

    def run(self, coro: Coroutine) -> Future:
        """
        Runs a coroutine in the background event loop and returns a Future with error handling.
        In fallback mode, runs synchronously.
        """
        if self._shutdown:
            raise AsyncRunnerShutdownError("AsyncRunner has been shut down")
            
        if self._initialization_failed:
            raise AsyncRunnerInitializationError("AsyncRunner initialization failed")
        
        self._stats['tasks_submitted'] += 1
        
        # Handle fallback mode (no thread/event loop)
        if self._fallback_mode:
            return self._run_fallback(coro)
            
        # Standard async mode
        if not self._loop:
            raise AsyncRunnerError("Event loop not initialized")
            
        if self._loop.is_closed():
            raise AsyncRunnerError("Event loop is closed")
            
        if not self._thread or not self._thread.is_alive():
            raise AsyncRunnerError("Background thread is not running")
            
        try:
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            
            # Wrap the future to track completion/failure
            original_result = future.result
            original_exception = future.exception
            
            def tracked_result(timeout=None):
                try:
                    result = original_result(timeout)
                    self._stats['tasks_completed'] += 1
                    return result
                except Exception:
                    self._stats['tasks_failed'] += 1
                    raise
            
            def tracked_exception(timeout=None):
                try:
                    exc = original_exception(timeout)
                    if exc is not None:
                        self._stats['tasks_failed'] += 1
                    return exc
                except Exception:
                    self._stats['tasks_failed'] += 1
                    raise
            
            future.result = tracked_result
            future.exception = tracked_exception
            
            return future
            
        except RuntimeError as e:
            self._stats['tasks_failed'] += 1
            logger.error(f"Failed to schedule coroutine: {e}")
            raise AsyncRunnerError(f"Failed to schedule coroutine: {e}") from e
        except Exception as e:
            self._stats['tasks_failed'] += 1
            logger.error(f"Unexpected error scheduling coroutine: {e}", exc_info=True)
            raise AsyncRunnerError(f"Unexpected error: {e}") from e
    
    def _run_fallback(self, coro: Coroutine) -> Future:
        """Run coroutine synchronously in fallback mode."""
        future = Future()
        try:
            # Try to run the coroutine synchronously
            try:
                # Check if we have an existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, can't use asyncio.run
                    logger.warning("Cannot run coroutine in fallback mode - already in async context")
                    future.set_exception(AsyncRunnerError("Cannot run coroutine in active event loop"))
                else:
                    result = loop.run_until_complete(coro)
                    future.set_result(result)
                    self._stats['tasks_completed'] += 1
            except RuntimeError:
                # No event loop, use asyncio.run
                result = asyncio.run(coro)
                future.set_result(result)
                self._stats['tasks_completed'] += 1
        except Exception as e:
            self._stats['tasks_failed'] += 1
            future.set_exception(e)
            logger.error(f"Fallback execution failed: {e}")
        
        return future

    def shutdown(self):
        """
        Shuts down the event loop and waits for the thread to join.
        """
        if self._shutdown:
            return
            
        logger.debug("Shutting down AsyncRunner")
        self._shutdown = True
        
        if self._loop and not self._loop.is_closed():
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except RuntimeError:
                # Loop might already be stopped
                pass
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                logger.warning("AsyncRunner thread did not shut down cleanly")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.shutdown()
        return None
    
    def __del__(self):
        """Cleanup when garbage collected."""
        if not self._shutdown:
            logger.warning("AsyncRunner was garbage collected without proper shutdown")
            self.shutdown()
    
    def is_healthy(self) -> bool:
        """Check if the AsyncRunner is in a healthy state."""
        if self._shutdown or self._initialization_failed:
            return False
        
        # In fallback mode, we're healthy if not shut down
        if self._fallback_mode:
            return True
            
        # In thread mode, check thread and loop status
        if not self._loop or self._loop.is_closed():
            return False
        if not self._thread or not self._thread.is_alive():
            return False
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics for the AsyncRunner."""
        return {
            **self._stats.copy(),
            'is_healthy': self.is_healthy(),
            'is_shutdown': self._shutdown,
            'initialization_failed': self._initialization_failed,
            'fallback_mode': self._fallback_mode,
            'thread_alive': self._thread.is_alive() if self._thread else False,
            'loop_closed': self._loop.is_closed() if self._loop else True,
        }
    
    def reset_stats(self):
        """Reset runtime statistics."""
        logger.debug("Resetting AsyncRunner statistics")
        self._stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'initialization_attempts': self._stats.get('initialization_attempts', 0)
        }
    
    @classmethod
    def cleanup_all(cls):
        """Clean up all AsyncRunner instances."""
        instances = list(cls._instances)
        logger.debug(f"Cleaning up {len(instances)} AsyncRunner instances")
        for instance in instances:
            try:
                instance.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down AsyncRunner instance: {e}")
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Any]:
        """Get statistics for all AsyncRunner instances."""
        instances = list(cls._instances)
        total_stats = {
            'instance_count': len(instances),
            'healthy_instances': 0,
            'total_tasks_submitted': 0,
            'total_tasks_completed': 0,
            'total_tasks_failed': 0,
            'total_initialization_attempts': 0
        }
        
        for instance in instances:
            try:
                stats = instance.get_stats()
                if stats['is_healthy']:
                    total_stats['healthy_instances'] += 1
                total_stats['total_tasks_submitted'] += stats['tasks_submitted']
                total_stats['total_tasks_completed'] += stats['tasks_completed']
                total_stats['total_tasks_failed'] += stats['tasks_failed']
                total_stats['total_initialization_attempts'] += stats['initialization_attempts']
            except Exception as e:
                logger.error(f"Error getting stats from AsyncRunner instance: {e}")
        
        return total_stats


# Register cleanup at exit
atexit.register(AsyncRunner.cleanup_all)

def st_coro(func: Callable[..., Coroutine]) -> Callable[..., None]:
    """
    A decorator to run a coroutine in the Streamlit session's async runner.
    It stores the future in the session state and reruns the page.
    """
    def wrapper(*args, **kwargs):
        try:
            import streamlit as st
        except ImportError:
            logger.error("Streamlit not available for st_coro decorator")
            return

        try:
            if "async_runner" not in st.session_state:
                st.session_state.async_runner = AsyncRunner()
                # Register cleanup hook
                register_streamlit_cleanup(st.session_state.async_runner)
            
            runner = st.session_state.async_runner
            
            # Create a unique key for the future based on function and arguments
            try:
                kwargs_hash = hash(frozenset(kwargs.items()))
            except TypeError:
                # Fallback for unhashable kwargs
                kwargs_hash = hash(str(sorted(kwargs.items())))
            
            future_key = f"future_{func.__name__}_{hash(args)}_{kwargs_hash}"
            
            # Run the coroutine and store the future
            future = runner.run(func(*args, **kwargs))
            st.session_state[future_key] = future
            
            # Rerun to enter the waiting state
            st.rerun()
            
        except Exception as e:
            logger.error(f"Error in st_coro wrapper: {e}")
            # Don't propagate error to avoid breaking Streamlit
            import streamlit as st
            st.error(f"Async operation failed: {e}")

    return wrapper


def register_streamlit_cleanup(runner: AsyncRunner):
    """
    Register cleanup hooks for Streamlit session.
    Note: This is a best-effort cleanup since Streamlit doesn't have 
    explicit session end hooks.
    """
    import streamlit as st
    
    # Store reference for manual cleanup if needed
    if "_async_runner_cleanup" not in st.session_state:
        st.session_state._async_runner_cleanup = []
    st.session_state._async_runner_cleanup.append(runner)


def cleanup_streamlit_runners():
    """
    Manually clean up AsyncRunners from Streamlit session state.
    Should be called when the session needs to be reset.
    """
    try:
        import streamlit as st
        if "_async_runner_cleanup" in st.session_state:
            runners = st.session_state._async_runner_cleanup
            for runner in runners:
                try:
                    runner.shutdown()
                except Exception as e:
                    logger.error(f"Error cleaning up AsyncRunner: {e}")
            st.session_state._async_runner_cleanup.clear()
            logger.debug("Cleaned up Streamlit AsyncRunners")
    except ImportError:
        pass
    except Exception as e:
        logger.error(f"Error in cleanup_streamlit_runners: {e}")
