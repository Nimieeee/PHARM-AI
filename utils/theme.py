"""
Clean Light Theme System
"""

import streamlit as st

def get_light_theme_css():
    """Get clean light theme CSS for maximum readability."""
    return """
    <style>
        /* Force light mode for everything */
        .stApp {
            background-color: #ffffff !important;
            color: #1a202c !important;
            color-scheme: light !important;
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
        
        /* Chat messages */
        .stChatMessage {
            background-color: #f8fafc !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            color: #1a202c !important;
            margin: 8px 0 !important;
            padding: 12px !important;
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
    """Apply the clean light theme CSS."""
    st.markdown(get_light_theme_css(), unsafe_allow_html=True)