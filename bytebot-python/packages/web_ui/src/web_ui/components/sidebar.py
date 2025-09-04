"""Sidebar navigation component."""

import streamlit as st


def render_sidebar() -> str:
    """Render sidebar navigation and return selected page."""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/1e3a8a/ffffff?text=Bytebot", width=200)
        
        st.markdown("---")
        
        # Navigation
        page = st.selectbox(
            "📍 Navigate",
            ["Tasks & Desktop", "Live Desktop View", "Settings"],
            index=0
        )
        
        st.markdown("---")
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("📷 Take Screenshot", use_container_width=True):
            st.session_state.take_screenshot = True
        
        if st.button("🔄 Refresh All", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        
        # System Status
        st.subheader("🟢 System Status")
        st.success("AI Agent: Online")
        st.success("Desktop: Online")
        st.info("Database: Connected")
        
        return page