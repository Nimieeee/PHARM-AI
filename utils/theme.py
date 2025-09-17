"""
Responsive Theme System with Dark Mode Support
"""

import streamlit as st

def get_system_aware_theme_css():
    """Get CSS that respects system dark/light mode preference."""
    return """
    <style>
        /* Default light theme */
        :root {
            --bg-color: #ffffff;
            --text-color: #1f2937;
            --sidebar-bg: #f8fafc;
            --border-color: #e5e7eb;
        }
        
        /* Dark theme when system prefers dark */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #111827;
                --text-color: #f8fafc;
                --sidebar-bg: #1f2937;
                --border-color: #4b5563;
            }
        }
        
        /* Apply CSS variables */
        .stApp {
            background-color: var(--bg-color) !important;
            color: var(--text-color) !important;
        }
        
        .stSidebar {
            background-color: var(--sidebar-bg) !important;
            border-right: 1px solid var(--border-color) !important;
        }
        
        .stMarkdown {
            color: var(--text-color) !important;
            font-size: 16px !important;
            line-height: 1.8 !important;
        }
        
        /* Include base responsive styles */
    """ + get_responsive_theme_css().replace('<style>', '').replace('</style>', '') + """
    </style>
    """

def get_dark_theme_css():
    """Get dark theme CSS optimized for readability and mobile."""
    return """
    <style>
        /* Dark Mode Styles - Improved Readability */
        .stApp {
            background-color: #111827 !important;
            color: #f9fafb !important;
            color-scheme: dark !important;
        }
        
        .stSidebar {
            background-color: #1f2937 !important;
            border-right: 1px solid #4b5563 !important;
        }
        
        .stSidebar .stMarkdown {
            color: #f3f4f6 !important;
        }
        
        /* Dark mode buttons - Better contrast */
        .stButton > button {
            background-color: #374151 !important;
            color: #f9fafb !important;
            border: 1px solid #6b7280 !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
        }
        
        .stButton > button:hover {
            background-color: #4b5563 !important;
            border-color: #8b5cf6 !important;
            color: #ffffff !important;
        }
        
        .stButton > button[kind="primary"] {
            background-color: #7c3aed !important;
            color: #ffffff !important;
            border: 1px solid #7c3aed !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            background-color: #6d28d9 !important;
        }
        
        /* Dark mode form elements - Better readability */
        .stTextInput > div > div > input {
            background-color: #374151 !important;
            color: #f9fafb !important;
            border: 1px solid #6b7280 !important;
            border-radius: 8px !important;
            padding: 16px !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #8b5cf6 !important;
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.3) !important;
            background-color: #4b5563 !important;
        }
        
        .stTextArea > div > div > textarea {
            background-color: #374151 !important;
            color: #f9fafb !important;
            border: 1px solid #6b7280 !important;
            border-radius: 8px !important;
            padding: 16px !important;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #8b5cf6 !important;
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.3) !important;
            background-color: #4b5563 !important;
        }
        
        .stSelectbox > div > div {
            background-color: #374151 !important;
            color: #f9fafb !important;
            border: 1px solid #6b7280 !important;
            padding: 16px !important;
            border-radius: 8px !important;
        }
        
        /* Dark mode chat messages - Enhanced readability */
        .stChatMessage {
            background-color: #374151 !important;
            border: 1px solid #6b7280 !important;
            color: #f9fafb !important;
            padding: 20px 24px !important;
            margin: 16px 0 !important;
            line-height: 1.7 !important;
            font-size: 16px !important;
            border-radius: 12px !important;
        }
        
        .stChatMessage[data-testid="chat-message-user"] {
            background-color: #3730a3 !important;
            border-color: #4f46e5 !important;
            color: #e0e7ff !important;
        }
        
        .stChatMessage[data-testid="chat-message-assistant"] {
            background-color: #065f46 !important;
            border-color: #10b981 !important;
            color: #d1fae5 !important;
        }
        
        /* Dark mode file uploader - Better visibility */
        .stFileUploader > div {
            background-color: #374151 !important;
            border: 2px dashed #9ca3af !important;
            color: #f3f4f6 !important;
            padding: 1.5rem !important;
        }
        
        .stFileUploader > div:hover {
            border-color: #8b5cf6 !important;
            background-color: #4b5563 !important;
        }
        
        /* Dark mode typography - Enhanced readability */
        .stMarkdown {
            color: #f8fafc !important;
            line-height: 1.8 !important;
            font-size: 16px !important;
        }
        
        .stMarkdown p {
            margin-bottom: 1.25rem !important;
            font-size: 16px !important;
            line-height: 1.8 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            margin-bottom: 1rem !important;
            margin-top: 2rem !important;
            font-weight: 600 !important;
        }
        
        /* Better text contrast */
        .stMarkdown strong {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        .stMarkdown em {
            color: #e2e8f0 !important;
        }
        
        /* Better code blocks in dark mode */
        code {
            background-color: #4b5563 !important;
            color: #f9fafb !important;
            padding: 0.25rem 0.5rem !important;
            border-radius: 4px !important;
        }
        
        /* Dark mode alerts */
        .stSuccess {
            background-color: #064e3b !important;
            border: 1px solid #059669 !important;
            color: #10b981 !important;
        }
        
        .stError {
            background-color: #7f1d1d !important;
            border: 1px solid #dc2626 !important;
            color: #f87171 !important;
        }
        
        .stInfo {
            background-color: #1e3a8a !important;
            border: 1px solid #3b82f6 !important;
            color: #60a5fa !important;
        }
        
        .stWarning {
            background-color: #92400e !important;
            border: 1px solid #f59e0b !important;
            color: #fbbf24 !important;
        }
        
        /* Mobile dark mode optimizations */
        @media (max-width: 768px) {
            .stApp {
                background-color: #0f172a !important;
            }
            
            .stChatInputContainer {
                background: transparent !important;
                border: none !important;
                padding: 16px 0 !important;
            }
            
            /* Dark mode chat input field */
            .stChatInput > div > div > div > div {
                background: #374151 !important;
                border: 2px solid #6b7280 !important;
                color: #f9fafb !important;
                border-radius: 12px !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            }
            
            .stChatInput > div > div > div > div:focus {
                border-color: #8b5cf6 !important;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
            }
            
            /* Better mobile readability in dark mode */
            .stChatMessage {
                padding: 1.25rem !important;
                margin: 1rem 0 !important;
                font-size: 16px !important;
            }
            
            .stMarkdown {
                font-size: 15px !important;
                line-height: 1.7 !important;
            }
        }
    </style>
    """

def get_responsive_theme_css():
    """Get responsive theme CSS optimized for mobile and desktop."""
    return """
    <style>
        /* Mobile-First Responsive Design */
        .stApp {
            background-color: #ffffff !important;
            color: #1a202c !important;
            color-scheme: light !important;
        }
        
        /* Enhanced padding and spacing - 16px base */
        .main .block-container {
            padding-top: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-bottom: 4rem !important;
            max-width: none !important;
        }
        
        /* Remove app padding that creates boundaries */
        .stApp {
            padding: 0 !important;
        }
        
        /* Ensure full width for chat */
        .stChatInput {
            width: 100% !important;
        }
        
        /* Better component spacing */
        .stButton > button {
            padding: 16px 24px !important;
            margin: 8px 0 !important;
        }
        
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            padding: 16px !important;
        }
        
        .stChatMessage {
            padding: 16px 20px !important;
            margin: 12px 0 !important;
        }
        
        /* Mobile viewport optimization */
        @media (max-width: 768px) {
            .stApp {
                padding: 0.75rem !important;
            }
            
            .main .block-container {
                padding-top: 1.5rem !important;
                padding-left: 1.5rem !important;
                padding-right: 1.5rem !important;
                max-width: 100% !important;
            }
            
            /* Hide Streamlit branding on mobile */
            .stDeployButton {
                display: none !important;
            }
            
            /* Optimize header on mobile */
            header[data-testid="stHeader"] {
                height: 2.5rem !important;
            }
            
            /* Mobile navigation improvements */
            .stSidebarNav {
                padding: 16px !important;
            }
            
            /* Better mobile menu */
            .stSidebar .stButton > button {
                width: 100% !important;
                text-align: left !important;
                justify-content: flex-start !important;
            }
            
            /* Mobile-friendly toggles */
            .stToggle {
                padding: 8px 0 !important;
            }
            
            /* Mobile sidebar improvements */
            .stSidebar {
                width: 100% !important;
            }
            
            /* Mobile button improvements */
            .stButton > button {
                width: 100% !important;
                padding: 0.75rem 1rem !important;
                font-size: 16px !important; /* Prevents zoom on iOS */
                min-height: 44px !important; /* Touch target size */
            }
            
            /* Mobile input improvements */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea {
                font-size: 16px !important; /* Prevents zoom on iOS */
                padding: 0.75rem !important;
            }
            
            /* Mobile chat message improvements */
            .stChatMessage {
                margin: 16px 0 !important;
                padding: 18px 20px !important;
                font-size: 16px !important;
                line-height: 1.7 !important;
            }
            
            /* Mobile chat input improvements */
            .stChatInput > div > div > div > div {
                padding: 16px 20px !important;
                font-size: 16px !important;
                min-height: 48px !important;
            }
            
            /* Mobile file uploader */
            .stFileUploader > div {
                padding: 1.5rem !important;
                min-height: 80px !important;
            }
            
            /* Mobile form improvements - 16px base */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea {
                padding: 16px !important;
                font-size: 16px !important;
                min-height: 48px !important; /* Better touch targets */
            }
            
            /* Mobile button improvements - 16px base */
            .stButton > button {
                padding: 16px 24px !important;
                margin: 8px 0 !important;
                min-height: 48px !important; /* Better touch targets */
            }
            
            /* Mobile sidebar improvements */
            .stSidebar {
                padding: 16px !important;
            }
            
            /* Mobile selectbox improvements */
            .stSelectbox > div > div {
                padding: 16px !important;
                min-height: 48px !important;
            }
        }
        
        /* Tablet optimizations */
        @media (min-width: 769px) and (max-width: 1024px) {
            .main .block-container {
                max-width: 90% !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }
        }
        
        /* Desktop optimizations */
        @media (min-width: 1025px) {
            .main .block-container {
                max-width: 1200px !important;
            }
        }
        
        /* Performance optimizations */
        * {
            box-sizing: border-box !important;
        }
        
        /* Smooth transitions */
        .stButton > button,
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div {
            transition: all 0.2s ease !important;
        }
        
        /* Optimize scrolling */
        .main {
            scroll-behavior: smooth !important;
        }
        
        /* Reduce layout shift */
        .stChatMessage {
            min-height: 2rem !important;
        }
        
        /* Optimize images */
        img {
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* Mobile-optimized tables */
        .stDataFrame {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }
        
        @media (max-width: 768px) {
            /* Mobile table optimizations */
            .stDataFrame table {
                font-size: 12px !important;
                min-width: 100% !important;
            }
            
            .stDataFrame th,
            .stDataFrame td {
                padding: 0.5rem 0.25rem !important;
                white-space: nowrap !important;
            }
            
            /* Stack table cells on very small screens */
            @media (max-width: 480px) {
                .stDataFrame table,
                .stDataFrame thead,
                .stDataFrame tbody,
                .stDataFrame th,
                .stDataFrame td,
                .stDataFrame tr {
                    display: block !important;
                }
                
                .stDataFrame thead tr {
                    position: absolute !important;
                    top: -9999px !important;
                    left: -9999px !important;
                }
                
                .stDataFrame tr {
                    border: 1px solid #e5e7eb !important;
                    margin-bottom: 0.5rem !important;
                    padding: 0.5rem !important;
                    border-radius: 8px !important;
                }
                
                .stDataFrame td {
                    border: none !important;
                    position: relative !important;
                    padding-left: 50% !important;
                    white-space: normal !important;
                }
                
                .stDataFrame td:before {
                    content: attr(data-label) ": " !important;
                    position: absolute !important;
                    left: 6px !important;
                    width: 45% !important;
                    padding-right: 10px !important;
                    white-space: nowrap !important;
                    font-weight: bold !important;
                }
            }
        }
        
        /* Enhanced readability for light mode */
        .stMarkdown {
            font-size: 16px !important;
            line-height: 1.8 !important;
            color: #1f2937 !important;
        }
        
        .stMarkdown p {
            margin-bottom: 1.25rem !important;
            font-size: 16px !important;
            line-height: 1.8 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            margin-bottom: 1rem !important;
            margin-top: 2rem !important;
            font-weight: 600 !important;
            color: #111827 !important;
        }
        
        /* Better focus indicators */
        .stButton > button:focus,
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            outline: 2px solid #6366f1 !important;
            outline-offset: 2px !important;
        }
        
        /* Seamless chat input - part of the page */
        .stChatInputContainer {
            background: transparent !important;
            border: none !important;
            border-radius: 0 !important;
            padding: 16px 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
            position: relative !important;
        }
        
        /* Style the actual input field */
        .stChatInput > div > div > div > div {
            background: #ffffff !important;
            border: 2px solid #e5e7eb !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            font-size: 16px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
        }
        
        .stChatInput > div > div > div > div:focus {
            border-color: #6366f1 !important;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
        }
        
        /* Accessibility improvements */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        .stSidebar {
            background-color: #f8fafc !important;
            border-right: 1px solid #e2e8f0 !important;
        }
        
        .stSidebar .stMarkdown {
            color: #2d3748 !important;
        }
        
        /* Clean button styling */
        .stButton > button {
            background-color: #ffffff !important;
            color: #2d3748 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button:hover {
            background-color: #f9fafb !important;
            border-color: #667eea !important;
            color: #1a202c !important;
        }
        
        .stButton > button[kind="primary"] {
            background-color: #667eea !important;
            color: #ffffff !important;
            border: 1px solid #667eea !important;
            font-weight: 600 !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            background-color: #5a67d8 !important;
            border-color: #5a67d8 !important;
        }
        
        .stButton > button[kind="secondary"] {
            background-color: #f8fafc !important;
            color: #374151 !important;
            border: 1px solid #d1d5db !important;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background-color: #f1f5f9 !important;
            border-color: #9ca3af !important;
        }
        
        /* Form elements */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #1a202c !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            font-size: 14px !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1) !important;
        }
        
        .stTextArea > div > div > textarea {
            background-color: #ffffff !important;
            color: #1a202c !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            font-size: 14px !important;
        }
        
        .stTextArea > div > div > textarea:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1) !important;
        }
        
        .stSelectbox > div > div {
            background-color: #ffffff !important;
            color: #1a202c !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
        }
        
        /* File uploader */
        .stFileUploader > div {
            background-color: #f8fafc !important;
            border: 2px dashed #9ca3af !important;
            border-radius: 8px !important;
            color: #374151 !important;
        }
        
        .stFileUploader > div:hover {
            border-color: #667eea !important;
            background-color: #f1f5f9 !important;
        }
        
        /* Alert boxes */
        .stSuccess {
            background-color: #f0fdf4 !important;
            border: 1px solid #22c55e !important;
            border-radius: 8px !important;
            color: #15803d !important;
        }
        
        .stError {
            background-color: #fef2f2 !important;
            border: 1px solid #ef4444 !important;
            border-radius: 8px !important;
            color: #dc2626 !important;
        }
        
        .stInfo {
            background-color: #eff6ff !important;
            border: 1px solid #3b82f6 !important;
            border-radius: 8px !important;
            color: #1d4ed8 !important;
        }
        
        .stWarning {
            background-color: #fffbeb !important;
            border: 1px solid #f59e0b !important;
            border-radius: 8px !important;
            color: #d97706 !important;
        }
        
        /* Chat messages - Enhanced readability */
        .stChatMessage {
            background-color: #f8fafc !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            color: #1f2937 !important;
            margin: 16px 0 !important;
            padding: 20px 24px !important;
            font-size: 16px !important;
            line-height: 1.7 !important;
        }
        
        .stChatMessage[data-testid="chat-message-user"] {
            background-color: #eff6ff !important;
            border-color: #bfdbfe !important;
        }
        
        .stChatMessage[data-testid="chat-message-assistant"] {
            background-color: #f0fdf4 !important;
            border-color: #bbf7d0 !important;
        }
        
        /* Toggle switches */
        .stToggle > div > div > div > div {
            background-color: #d1d5db !important;
        }
        
        .stToggle > div > div > div > div[data-checked="true"] {
            background-color: #667eea !important;
        }
        
        .stToggle > div > label {
            color: #374151 !important;
            font-weight: 500 !important;
        }
        
        /* Typography */
        .stMarkdown {
            color: #374151 !important;
        }
        
        .stMarkdown p {
            color: #374151 !important;
            line-height: 1.6 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #1a202c !important;
            font-weight: 600 !important;
            line-height: 1.3 !important;
        }
        
        /* Code blocks */
        .stCode {
            background-color: #f8fafc !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 8px !important;
            color: #1a202c !important;
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background-color: #f8fafc !important;
            color: #374151 !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        
        .streamlit-expanderContent {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 0 0 8px 8px !important;
            color: #374151 !important;
        }
        
        /* Sidebar elements */
        .stSidebar .stButton > button {
            background-color: #ffffff !important;
            color: #374151 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 6px !important;
        }
        
        .stSidebar .stButton > button:hover {
            background-color: #f1f5f9 !important;
            border-color: #9ca3af !important;
        }
        
        /* Forms */
        .stForm {
            background-color: #f8fafc !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #f8fafc !important;
            border-radius: 8px !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #6b7280 !important;
            background-color: transparent !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #667eea !important;
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Metrics */
        .stMetric {
            background-color: #f8fafc !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 8px !important;
            color: #1a202c !important;
        }
        
        /* DataFrames */
        .stDataFrame {
            background-color: #ffffff !important;
            color: #1a202c !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 8px !important;
        }
        
        /* Ensure all text is readable */
        * {
            color-scheme: light !important;
        }
        
        /* Override any dark mode preferences */
        @media (prefers-color-scheme: dark) {
            .stApp {
                background-color: #ffffff !important;
                color: #1a202c !important;
            }
            
            .stSidebar {
                background-color: #f8fafc !important;
            }
            
            .stMarkdown {
                color: #374151 !important;
            }
            
            h1, h2, h3, h4, h5, h6 {
                color: #1a202c !important;
            }
        }
    </style>
    """

def apply_theme():
    """Apply the selected theme with system fallback."""
    # Check if user has set a preference, otherwise use system
    if 'dark_mode' in st.session_state:
        # User has made a choice
        if st.session_state.dark_mode:
            st.markdown(get_dark_theme_css(), unsafe_allow_html=True)
        else:
            st.markdown(get_responsive_theme_css(), unsafe_allow_html=True)
    else:
        # No user preference, use system-aware theme
        st.markdown(get_system_aware_theme_css(), unsafe_allow_html=True)

def render_theme_toggle():
    """Render simple and reliable theme toggle."""
    with st.sidebar:
        st.markdown("### 🎨 Theme")
        
        # Simple toggle between light and dark
        dark_mode = st.toggle(
            "🌙 Dark Mode",
            value=st.session_state.get('dark_mode', False),
            help="Toggle between light and dark themes"
        )
        
        # Update session state if changed
        if dark_mode != st.session_state.get('dark_mode', False):
            st.session_state.dark_mode = dark_mode
            # Remove old theme preference
            if 'theme_preference' in st.session_state:
                del st.session_state.theme_preference
            st.rerun()
        
        st.markdown("---")

def create_responsive_columns(mobile_cols=1, tablet_cols=2, desktop_cols=3):
    """Create responsive columns based on screen size."""
    # Use CSS to detect screen size and adjust accordingly
    st.markdown("""
    <style>
    .responsive-container {
        display: grid;
        gap: 1rem;
        grid-template-columns: 1fr;
    }
    
    @media (min-width: 768px) {
        .responsive-container {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (min-width: 1024px) {
        .responsive-container {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Return standard Streamlit columns for now
    return st.columns(desktop_cols)

def add_mobile_meta_tags():
    """Add mobile-specific meta tags for better mobile experience."""
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="theme-color" content="#6366f1">
    """, unsafe_allow_html=True)

# Keep backward compatibility
def get_light_theme_css():
    """Backward compatibility - returns responsive light theme."""
    return get_responsive_theme_css()