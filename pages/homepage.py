"""
Homepage - Landing Page
"""

import streamlit as st

def render_homepage():
    """Render the homepage."""
    st.markdown("# 💊 PharmBot")
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
    st.markdown("### ✨ What Makes PharmBot Special")
    
    # Add custom CSS for highly readable interactive cards
    st.markdown("""
    <style>
    /* Base styling for feature cards with maximum readability */
    div[data-testid="column"] button[kind="secondary"] {
        border: 3px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px !important;
        padding: 30px 25px !important;
        text-align: center !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.3s ease !important;
        height: 200px !important;
        font-size: 1.1rem !important;
        line-height: 1.6 !important;
        white-space: pre-line !important;
        font-weight: 600 !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    div[data-testid="column"] button[kind="secondary"]:hover {
        transform: translateY(-8px) !important;
        box-shadow: 0 15px 50px rgba(0, 0, 0, 0.25) !important;
    }
    
    /* Deep Knowledge card - Enhanced Blue gradient */
    button[key="deep_knowledge_card"] {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%) !important;
        color: #ffffff !important;
        border: 3px solid rgba(30, 64, 175, 0.4) !important;
    }
    
    button[key="deep_knowledge_card"]:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        border: 3px solid rgba(59, 130, 246, 0.6) !important;
    }
    
    /* Instant Answers card - Enhanced Orange gradient */
    button[key="instant_answers_card"] {
        background: linear-gradient(135deg, #dc2626 0%, #f59e0b 100%) !important;
        color: #ffffff !important;
        border: 3px solid rgba(220, 38, 38, 0.4) !important;
    }
    
    button[key="instant_answers_card"]:hover {
        background: linear-gradient(135deg, #ef4444 0%, #fbbf24 100%) !important;
        border: 3px solid rgba(239, 68, 68, 0.6) !important;
    }
    
    /* Personalized Learning card - Enhanced Green gradient */
    button[key="personalized_learning_card"] {
        background: linear-gradient(135deg, #047857 0%, #0891b2 100%) !important;
        color: #ffffff !important;
        border: 3px solid rgba(4, 120, 87, 0.4) !important;
    }
    
    button[key="personalized_learning_card"]:hover {
        background: linear-gradient(135deg, #059669 0%, #0ea5e9 100%) !important;
        border: 3px solid rgba(5, 150, 105, 0.6) !important;
    }
    
    /* Maximum text readability with strong shadows and contrast */
    button[key="deep_knowledge_card"] span,
    button[key="instant_answers_card"] span,
    button[key="personalized_learning_card"] span {
        color: #ffffff !important;
        text-shadow: 
            0 2px 4px rgba(0, 0, 0, 0.5),
            0 1px 2px rgba(0, 0, 0, 0.8) !important;
        font-weight: 700 !important;
        display: block !important;
        text-align: center !important;
    }
    
    /* Add subtle background pattern for better text separation */
    button[key="deep_knowledge_card"]::before,
    button[key="instant_answers_card"]::before,
    button[key="personalized_learning_card"]::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background: rgba(0, 0, 0, 0.1) !important;
        z-index: 0 !important;
    }
    
    /* Ensure text is above the overlay */
    button[key="deep_knowledge_card"] span,
    button[key="instant_answers_card"] span,
    button[key="personalized_learning_card"] span {
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Demo section styling with better contrast */
    .demo-section {
        background: rgba(102, 126, 234, 0.12);
        border-radius: 15px;
        padding: 25px;
        margin: 25px 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
    }
    
    /* Dark mode adjustments for better visibility */
    @media (prefers-color-scheme: dark) {
        .demo-section {
            background: rgba(102, 126, 234, 0.18);
            border-left-color: #8b5cf6;
            box-shadow: 0 4px 20px rgba(139, 92, 246, 0.15);
        }
        
        /* Enhance card contrast in dark mode */
        button[key="deep_knowledge_card"] {
            background: linear-gradient(135deg, #1e3a8a 0%, #6b21a8 100%) !important;
        }
        
        button[key="instant_answers_card"] {
            background: linear-gradient(135deg, #b91c1c 0%, #d97706 100%) !important;
        }
        
        button[key="personalized_learning_card"] {
            background: linear-gradient(135deg, #065f46 0%, #0e7490 100%) !important;
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
    
    # Key features
    st.markdown("### 🔬 Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔬 Evidence-Based")
        st.write("All information is grounded in scientific literature and current pharmaceutical knowledge.")
        
        st.markdown("#### 🎓 Educational") 
        st.write("Designed specifically for learning, with clear explanations and clinical context.")
        
        st.markdown("#### 💬 Interactive")
        st.write("Engage in natural conversations and ask follow-up questions for deeper understanding.")
    
    with col2:
        st.markdown("#### 📚 Document Upload")
        st.write("Upload your own research papers, textbooks, or notes to get personalized insights.")
        
        st.markdown("#### 🔍 Smart Search")
        st.write("Advanced search capabilities to find relevant information from your uploaded documents.")
        
        st.markdown("#### 💾 Conversation History")
        st.write("Keep track of your learning journey with persistent conversation history.")
    
    # Interactive example questions
    st.markdown("### 💡 Try These Example Questions")
    
    examples = [
        {
            "question": "Explain the mechanism of action of ACE inhibitors",
            "preview": "ACE inhibitors work by blocking the angiotensin-converting enzyme, which prevents the conversion of angiotensin I to angiotensin II..."
        },
        {
            "question": "What are the contraindications for NSAIDs?",
            "preview": "Major contraindications include active GI bleeding, severe heart failure, severe renal impairment, and known hypersensitivity..."
        },
        {
            "question": "How do beta-blockers work in treating hypertension?",
            "preview": "Beta-blockers reduce blood pressure through multiple mechanisms: decreased heart rate, reduced cardiac output, and decreased renin release..."
        },
        {
            "question": "Describe the pharmacokinetics of warfarin",
            "preview": "Warfarin is well absorbed orally, highly protein-bound (99%), metabolized by CYP2C9 and CYP3A4, with a half-life of 36-42 hours..."
        },
        {
            "question": "What drug interactions should I be aware of with statins?",
            "preview": "Key interactions include CYP3A4 inhibitors (increasing statin levels), fibrates (increased myopathy risk), and warfarin (enhanced anticoagulation)..."
        }
    ]
    
    for i, example in enumerate(examples):
        with st.expander(f"💬 {example['question']}", expanded=False):
            st.info(f"**Sample Response Preview:**\n\n{example['preview']}")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Try This Question", key=f"try_question_btn_{i}", type="secondary"):
                    st.session_state.current_page = "signin"
                    st.rerun()
    
    # Footer with disclaimer
    st.markdown("---")
    st.error("⚠️ **Important Disclaimer**: PharmBot is designed for educational purposes only. The information provided should not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for clinical decisions and patient care.")