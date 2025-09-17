"""
Clean Light Theme System
"""

import streamlit as st

def get_light_theme_css():
    """Get clean light theme CSS for maximum readability."""
    return """
    <style>
        /* Apple San Francisco Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global font family - Apple San Francisco with fallbacks */
        * {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
        }
        
        /* Force light mode for everything */
        .stApp {
            background-color: #ffffff !important;
            color: #1a202c !important;
            color-scheme: light !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
        }
        
        .stSidebar {
            background-color: #f8fafc !important;
            border-right: 1px solid #e2e8f0 !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
        }
        
        .stSidebar .stMarkdown {
            color: #2d3748 !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
        }
        
        /* Clean button styling with San Francisco Font */
        .stButton > button {
            background-color: #ffffff !important;
            color: #2d3748 !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
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
        
        /* Form elements with San Francisco Font */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #1a202c !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px !important;
            font-size: 14px !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
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
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
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
        
        /* File uploader - Aggressive fix for overlapping text */
        .stFileUploader > div {
            background-color: #f8fafc !important;
            border: 2px dashed #9ca3af !important;
            border-radius: 8px !important;
            color: #374151 !important;
            position: relative !important;
            padding: 20px !important;
            min-height: 80px !important;
            overflow: visible !important;
        }
        
        .stFileUploader > div:hover {
            border-color: #667eea !important;
            background-color: #f1f5f9 !important;
        }
        
        /* Hide Material Icons text that's causing overlap */
        .stFileUploader *[class*="material-icons"],
        .stFileUploader *:contains("keyboard_arrow_down"),
        .stFileUploader span:contains("keyboard_arrow_down") {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }
        
        /* Alternative: Hide any text containing keyboard */
        .stFileUploader * {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
        }
        
        .stFileUploader *:not([data-testid]):not([class*="upload"]):not([class*="file"]) {
            color: transparent !important;
        }
        
        /* Force proper text display for upload text only */
        .stFileUploader [data-testid="stFileUploaderDropzone"] {
            position: relative !important;
            background: transparent !important;
        }
        
        .stFileUploader [data-testid="stFileUploaderDropzone"] * {
            color: #374151 !important;
        }
        
        /* Hide any pseudo-elements that might contain the keyboard text */
        .stFileUploader *::before,
        .stFileUploader *::after {
            content: none !important;
            display: none !important;
        }
        
        /* Specific fix for the upload text */
        .stFileUploader label,
        .stFileUploader [data-testid="stFileUploaderDropzone"] > div {
            position: relative !important;
            z-index: 10 !important;
            background: #f8fafc !important;
            padding: 10px !important;
            border-radius: 4px !important;
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
        
        /* Chat messages with San Francisco Font */
        .stChatMessage {
            background-color: #f8fafc !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            color: #1a202c !important;
            margin: 8px 0 !important;
            padding: 12px !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
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
        
        /* Typography with San Francisco Font */
        .stMarkdown {
            color: #374151 !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
        }
        
        .stMarkdown p {
            color: #374151 !important;
            line-height: 1.6 !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", "Inter", system-ui, sans-serif !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #1a202c !important;
            font-weight: 600 !important;
            line-height: 1.3 !important;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", "Inter", system-ui, sans-serif !important;
        }
        
        /* Specific heading weights for San Francisco style */
        h1 {
            font-weight: 700 !important;
            font-size: 2.25rem !important;
        }
        
        h2 {
            font-weight: 600 !important;
            font-size: 1.875rem !important;
        }
        
        h3 {
            font-weight: 600 !important;
            font-size: 1.5rem !important;
        }
        
        h4 {
            font-weight: 500 !important;
            font-size: 1.25rem !important;
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
        
        /* Ensure all text is readable and properly positioned */
        * {
            color-scheme: light !important;
        }
        
        /* Fix any general text overlap issues */
        .stApp * {
            position: relative !important;
        }
        
        /* Aggressive fix: Hide any element containing keyboard text */
        *:contains("keyboard") {
            display: none !important;
        }
        
        /* Hide Material Icons font */
        .material-icons,
        [class*="material-icons"],
        span[class*="material"],
        i[class*="material"] {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Hide any arrow down elements */
        *[class*="arrow"],
        *[class*="down"],
        *:contains("arrow_down"),
        *:contains("keyboard_arrow") {
            display: none !important;
        }
        
        /* Ensure proper text rendering */
        .stApp {
            text-rendering: optimizeLegibility !important;
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
        }
        
        /* Fix button text positioning */
        .stButton button span {
            position: relative !important;
            z-index: 1 !important;
        }
        
        /* Fix any pseudo-element overlaps */
        *::before, *::after {
            z-index: 0 !important;
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
    """Apply the clean light theme CSS."""
    st.markdown(get_light_theme_css(), unsafe_allow_html=True)