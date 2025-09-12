"""
Homepage - Landing Page
"""

import streamlit as st

def render_homepage():
    """Render the homepage."""
    st.markdown("# 💊 PharmGPT")
    st.markdown("### Your AI Pharmacology Expert")
    st.markdown("Get instant answers to complex pharmacology questions and enhance your understanding of medicinal science.")
    st.markdown("---")
    
    # Call-to-action buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Get Started - Sign In", key="main_cta_signin_button", use_container_width=True, type="primary"):
            st.session_state.current_page = "signin"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Features showcase
    st.markdown("### ✨ What Makes PharmGPT Special")
    
    # Add custom CSS for clean light mode cards
    st.markdown("""
    <style>
    /* Clean light mode feature cards */
    div[data-testid="column"] button[kind="secondary"] {
        background: #ffffff !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 16px !important;
        padding: 24px 20px !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        height: 180px !important;
        font-size: 1rem !important;
        line-height: 1.4 !important;
        white-space: pre-line !important;
        font-weight: 600 !important;
        position: relative !important;
        overflow: hidden !important;
        color: #374151 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
    }
    
    div[data-testid="column"] button[kind="secondary"]:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
        border-color: #d1d5db !important;
    }
    
    /* Deep Knowledge card - Blue theme */
    button[key="deep_knowledge_card"] {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
        border: 2px solid #3b82f6 !important;
        color: #1e40af !important;
    }
    
    button[key="deep_knowledge_card"]:hover {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
        border-color: #2563eb !important;
        color: #1d4ed8 !important;
    }
    
    /* Instant Answers card - Orange theme */
    button[key="instant_answers_card"] {
        background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%) !important;
        border: 2px solid #f97316 !important;
        color: #ea580c !important;
    }
    
    button[key="instant_answers_card"]:hover {
        background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%) !important;
        border-color: #ea580c !important;
        color: #c2410c !important;
    }
    
    /* Personalized Learning card - Green theme */
    button[key="personalized_learning_card"] {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%) !important;
        border: 2px solid #22c55e !important;
        color: #16a34a !important;
    }
    
    button[key="personalized_learning_card"]:hover {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%) !important;
        border-color: #16a34a !important;
        color: #15803d !important;
    }
    

    
    /* Maximum text readability - Multiple selectors for better targeting */
    button[key="deep_knowledge_card"],
    button[key="deep_knowledge_card"] *,
    button[key="deep_knowledge_card"] span,
    button[key="deep_knowledge_card"] div {
        color: #ffffff !important;
        text-shadow: 
            0 2px 4px rgba(0, 0, 0, 1),
            0 4px 8px rgba(0, 0, 0, 0.8),
            0 1px 2px rgba(0, 0, 0, 1) !important;
        font-weight: 800 !important;
        text-align: center !important;
        position: relative !important;
        z-index: 10 !important;
    }
    
    button[key="instant_answers_card"],
    button[key="instant_answers_card"] *,
    button[key="instant_answers_card"] span,
    button[key="instant_answers_card"] div {
        color: #ffffff !important;
        text-shadow: 
            0 2px 4px rgba(0, 0, 0, 1),
            0 4px 8px rgba(0, 0, 0, 0.8),
            0 1px 2px rgba(0, 0, 0, 1) !important;
        font-weight: 800 !important;
        text-align: center !important;
        position: relative !important;
        z-index: 10 !important;
    }
    
    button[key="personalized_learning_card"],
    button[key="personalized_learning_card"] *,
    button[key="personalized_learning_card"] span,
    button[key="personalized_learning_card"] div {
        color: #ffffff !important;
        text-shadow: 
            0 2px 4px rgba(0, 0, 0, 1),
            0 4px 8px rgba(0, 0, 0, 0.8),
            0 1px 2px rgba(0, 0, 0, 1) !important;
        font-weight: 800 !important;
        text-align: center !important;
        position: relative !important;
        z-index: 10 !important;
    }
    
    /* Ensure text is readable in light mode */
    .stButton > button[key="deep_knowledge_card"],
    .stButton > button[key="instant_answers_card"], 
    .stButton > button[key="personalized_learning_card"] {
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    /* Clean demo section for light mode */
    .demo-section {
        background: #f8fafc !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
        padding: 24px !important;
        margin: 24px 0 !important;
        color: #374151 !important;
    }
    
    /* Override any dark mode preferences for cards */
    @media (prefers-color-scheme: dark) {
        div[data-testid="column"] button[kind="secondary"] {
            background: #ffffff !important;
            border: 2px solid #e5e7eb !important;
            color: #374151 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
        }
        
        button[key="deep_knowledge_card"] {
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
            border: 2px solid #3b82f6 !important;
            color: #1e40af !important;
        }
        
        button[key="instant_answers_card"] {
            background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%) !important;
            border: 2px solid #f97316 !important;
            color: #ea580c !important;
        }
        
        button[key="personalized_learning_card"] {
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%) !important;
            border: 2px solid #22c55e !important;
            color: #16a34a !important;
        }
        
        .demo-section {
            background: #f8fafc !important;
            border-color: #e5e7eb !important;
            color: #374151 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧬\n\n**Deep Knowledge**\n\nComprehensive understanding of drug mechanisms, interactions, and pharmacokinetics backed by scientific literature.", 
                    key="deep_knowledge_card", use_container_width=True, help="Learn more about our comprehensive drug knowledge"):
            st.session_state.demo_section = "deep_knowledge"
            st.rerun()
    
    with col2:
        if st.button("⚡\n\n**Instant Answers**\n\nGet immediate responses to complex pharmacology questions with detailed explanations and clinical context.", 
                    key="instant_answers_card", use_container_width=True, help="Experience fast, accurate responses"):
            st.session_state.demo_section = "instant_answers"
            st.rerun()
    
    with col3:
        if st.button("🎯\n\n**Personalized Learning**\n\nUpload your own documents and get personalized insights tailored to your learning materials.", 
                    key="personalized_learning_card", use_container_width=True, help="Customize your learning experience"):
            st.session_state.demo_section = "personalized_learning"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Interactive demo section
    if "demo_section" not in st.session_state:
        st.session_state.demo_section = None
    
    # Show demo content based on card clicks
    if st.session_state.demo_section:
        st.markdown("---")
        if st.session_state.demo_section == "deep_knowledge":
            st.markdown("### 🧬 Deep Knowledge Demo")
            st.info("**Example Drug Lookup**: Try asking about 'warfarin interactions' and get comprehensive information about:")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("• **Mechanism of Action**\n• **Pharmacokinetics**\n• **Drug Interactions**")
            with col2:
                st.markdown("• **Contraindications**\n• **Monitoring Parameters**\n• **Clinical Considerations**")
            
        elif st.session_state.demo_section == "instant_answers":
            st.markdown("### ⚡ Instant Answers Demo")
            st.success("**Lightning Fast Responses**: Get answers in seconds to questions like:")
            st.markdown("• *'How do ACE inhibitors work?'*\n• *'What are the side effects of NSAIDs?'*\n• *'Explain beta-blocker selectivity'*")
            
        elif st.session_state.demo_section == "personalized_learning":
            st.markdown("### 🎯 Personalized Learning Demo")
            st.warning("**Upload Your Materials**: Enhance responses with your own:")
            st.markdown("• Research papers and studies\n• Textbook chapters\n• Lecture notes and slides\n• Clinical guidelines")
        
        if st.button("🚀 Try It Now - Sign In", key="demo_try_now_button", type="primary"):
            st.session_state.current_page = "signin"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Footer with disclaimer
    st.markdown("---")
    st.error("⚠️ **Important Disclaimer**: PharmGPT is designed for educational purposes only. The information provided should not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for clinical decisions and patient care.")