"""
Theme Management System
"""

import streamlit as st

def get_theme_css():
    """Get CSS for the current theme."""
    theme = st.session_state.get("theme_mode", "light")
    
    if theme == "dark":
        return """
        <style>
            /* Dark theme styles */
            .stApp {
                background-color: #0e1117;
                color: #fafafa;
            }
            
            .stSidebar {
                background-color: #262730;
            }
            
            .stButton > button {
                background-color: #262730;
                color: #fafafa;
                border: 1px solid #4a4a4a;
            }
            
            .stButton > button:hover {
                background-color: #3a3a3a;
                border-color: #667eea;
            }
            
            .stSelectbox > div > div {
                background-color: #262730;
                color: #fafafa;
            }
            
            .stTextInput > div > div > input {
                background-color: #262730;
                color: #fafafa;
                border: 1px solid #4a4a4a;
            }
            
            .stTextArea > div > div > textarea {
                background-color: #262730;
                color: #fafafa;
                border: 1px solid #4a4a4a;
            }
            
            .stFileUploader > div {
                background-color: #262730;
                border: 2px dashed #4a4a4a;
            }
            
            .stFileUploader > div:hover {
                border-color: #667eea;
            }
            
            .stAlert {
                background-color: #262730;
                border: 1px solid #4a4a4a;
            }
            
            .stSuccess {
                background-color: #1e3a1e;
                border: 1px solid #4caf50;
            }
            
            .stError {
                background-color: #3a1e1e;
                border: 1px solid #f44336;
            }
            
            .stInfo {
                background-color: #1e2a3a;
                border: 1px solid #2196f3;
            }
            
            .stWarning {
                background-color: #3a2e1e;
                border: 1px solid #ff9800;
            }
            
            /* Chat message styling */
            .stChatMessage {
                background-color: #262730;
                border: 1px solid #4a4a4a;
            }
            
            /* Feature cards for dark mode */
            .feature-card {
                background: #262730 !important;
                border-color: #4a4a4a !important;
                color: #fafafa !important;
            }
            
            /* Toggle switch styling for dark mode */
            .stToggle > div > div > div > div {
                background-color: #4a4a4a !important;
            }
            
            .stToggle > div > div > div > div[data-checked="true"] {
                background-color: #667eea !important;
            }
            
            /* Radio button styling for dark mode */
            .stRadio > div {
                background-color: transparent;
            }
            
            .stRadio > div > label {
                color: #fafafa;
            }
            
            /* Markdown text */
            .stMarkdown {
                color: #fafafa;
            }
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #fafafa !important;
            }
            
            /* Code blocks */
            .stCode {
                background-color: #1e1e1e;
                border: 1px solid #4a4a4a;
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                background-color: #262730;
                color: #fafafa;
            }
            
            .streamlit-expanderContent {
                background-color: #262730;
                border: 1px solid #4a4a4a;
            }
        </style>
        """
    else:
        return """
        <style>
            /* Light theme styles (default) */
            .stApp {
                background-color: #ffffff;
                color: #262730;
            }
            
            .stSidebar {
                background-color: #f0f2f6;
            }
            
            .stButton > button {
                background-color: #ffffff;
                color: #262730;
                border: 1px solid #d0d0d0;
            }
            
            .stButton > button:hover {
                background-color: #f0f2f6;
                border-color: #667eea;
            }
            
            .stSelectbox > div > div {
                background-color: #ffffff;
                color: #262730;
            }
            
            .stTextInput > div > div > input {
                background-color: #ffffff;
                color: #262730;
                border: 1px solid #d0d0d0;
            }
            
            .stTextArea > div > div > textarea {
                background-color: #ffffff;
                color: #262730;
                border: 1px solid #d0d0d0;
            }
            
            .stFileUploader > div {
                background-color: #ffffff;
                border: 2px dashed #d0d0d0;
            }
            
            .stFileUploader > div:hover {
                border-color: #667eea;
            }
            
            /* Feature cards for light mode */
            .feature-card {
                background: #ffffff !important;
                border-color: #e0e0e0 !important;
                color: #262730 !important;
            }
            
            /* Toggle switch styling for light mode */
            .stToggle > div > div > div > div {
                background-color: #d0d0d0 !important;
            }
            
            .stToggle > div > div > div > div[data-checked="true"] {
                background-color: #667eea !important;
            }
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {
                color: #262730 !important;
            }
        </style>
        """

def render_theme_toggle():
    """Render the theme toggle switch."""
    current_theme = st.session_state.get("theme_mode", "light")
    is_dark = current_theme == "dark"
    
    # Theme toggle
    dark_mode = st.toggle(
        "🌙 Dark Mode", 
        value=is_dark,
        help="Switch between light and dark themes",
        key="theme_toggle"
    )
    
    # Update theme if changed
    new_theme = "dark" if dark_mode else "light"
    if new_theme != current_theme:
        st.session_state.theme_mode = new_theme
        st.rerun()

def apply_theme():
    """Apply the current theme CSS."""
    st.markdown(get_theme_css(), unsafe_allow_html=True)