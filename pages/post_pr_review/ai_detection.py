"""
AI detection questions page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, slider_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context, record_audio
from survey_questions import AI_DETECTION_QUESTIONS
from survey_data import save_post_pr_review_responses

# AI detection slider options (1-5 with labels)
AI_DETECTION_OPTIONS = ["Not selected", "1 - Definitely not", "2", "3", "4", "5 - Definitely yes"]


def ai_detection_page():
    """Display the AI detection questions page."""
    page_header(
        "AI-Generated Code Detection"
    )
    
    # Display PR context if available
    pr_url = st.session_state['survey_responses'].get('pr_url')
    issue_url = st.session_state['survey_responses'].get('issue_url')
    display_pr_context(pr_url=pr_url, issue_url=issue_url)

    # Load previous responses
    previous_ai_likelihood = st.session_state['survey_responses'].get('ai_likelihood')
    previous_ai_reasoning = st.session_state['survey_responses'].get('ai_reasoning', '')
    
    # AI likelihood question
    ai_likelihood = slider_question(
        AI_DETECTION_QUESTIONS['ai_likelihood'],
        AI_DETECTION_OPTIONS,
        "ai_likelihood",
        previous_ai_likelihood if previous_ai_likelihood else "Not selected",
        font_weight=600
    )
    
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    # AI reasoning question with audio or text option
    st.markdown(
        f"<p style='font-size:18px; font-weight:600; margin-bottom: 1.5rem;'>{AI_DETECTION_QUESTIONS['ai_reasoning']}</p>", 
        unsafe_allow_html=True
    )
    
    # Create tabs for audio and text input
    tab1, tab2 = st.tabs(["🎤 Record Audio", "⌨️ Type Response"])
    
    with tab1:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Click the microphone button below to record your response. Your audio will be transcribed automatically.
            </p>
            """, unsafe_allow_html=True)
        transcript = record_audio("ai_reasoning", min_duration=10, max_duration=180)
    
    with tab2:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Type your response in the text box below.
            </p>
            """, unsafe_allow_html=True)
        text_response = st.text_area(
            "Your response:",
            key="ai_reasoning_text",
            value=previous_ai_reasoning,
            height=150,
            placeholder="Type your answer here...",
            label_visibility="collapsed"
        )
    
    # Use whichever response is available
    if transcript:
        ai_reasoning = transcript
    elif text_response and text_response.strip():
        ai_reasoning = text_response
    else:
        ai_reasoning = previous_ai_reasoning
    
    # Validation function
    def validate():
        return ai_likelihood != "Not selected" and ai_reasoning.strip() != ""
    
    # Handlers with DB save on next (end of Post-PR-Review section)
    def handle_back():
        save_and_navigate('back', ai_likelihood=ai_likelihood, ai_reasoning=ai_reasoning)

    def handle_next():
        if not validate():
            return
        # Save current answers to session
        st.session_state['survey_responses']['ai_likelihood'] = ai_likelihood
        st.session_state['survey_responses']['ai_reasoning'] = ai_reasoning

        participant_id = st.session_state['survey_responses'].get('participant_id')
        pr_number = st.session_state['survey_responses'].get('pr_number', 'N/A')
        pr_title = st.session_state['survey_responses'].get('pr_title', 'N/A')
        pr_url = st.session_state['survey_responses'].get('pr_url', 'N/A')

        if participant_id:
            with st.spinner('Saving your responses...'):
                result = save_post_pr_review_responses(
                    participant_id,
                    pr_number,
                    pr_title,
                    pr_url,
                    st.session_state['survey_responses']
                )
            if not result.get('success'):
                st.error(f"⚠️ Error saving responses: {result.get('error')}")
                return

        save_and_navigate('next')

    # Navigation
    # Replace Next with a Submit button
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        back_clicked = st.button("Back", key="ai_detection_back")
    with col3:
        submit_clicked = st.button("Submit", key="ai_detection_submit")

    if back_clicked:
        handle_back()
    elif submit_clicked:
        if validate():
            handle_next()
        else:
            st.error("Please answer both questions before proceeding.")
