"""
Collaboration questions page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, slider_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context, record_audio
from survey_data import save_post_pr_closed_responses
from survey_questions import COLLABORATION_QUESTIONS

# Collaboration slider options (1-5 with labels)
COLLABORATION_OPTIONS = ["Not selected", "1 - Strongly disagree", "2", "3", "4", "5 - Strongly agree"]


def collaboration_questions_page():
    """Display the collaboration questions page."""
    page_header(
        "Collaboration Assessment",
    )
    
    # Display PR context if available
    pr_url = st.session_state['survey_responses'].get('pr_url')
    issue_url = st.session_state['survey_responses'].get('issue_url')
    display_pr_context(pr_url=pr_url, issue_url=issue_url)
    
    st.markdown("""
        <p style='font-size:18px; font-weight: 600; margin-bottom: 2rem'>
        The following statements focus on your collaboration with the contributor during the PR review. 
        Please rate how much you agree or disagree with each statement:
        </p>
        """, unsafe_allow_html=True)
    
    # Load previous responses
    previous_responses = st.session_state['survey_responses'].get('collaboration_responses', {})
    previous_collaboration_description = st.session_state['survey_responses'].get('collaboration_description', '')
    
    # Collaboration rating questions
    responses = {}
    for key, question in COLLABORATION_QUESTIONS.items():
        previous_value = previous_responses.get(key, "Not selected")
        
        response = slider_question(
            question,
            COLLABORATION_OPTIONS,
            f"collaboration_{key}",
            previous_value
        )
        
        responses[key] = response
    
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    # Open-ended collaboration question with audio or text option
    st.markdown("""
        <p style='font-size:18px; font-weight:600; margin-bottom: 1.5rem;'>
        How would you describe collaboration during code review overall? What helped or hindered communication with the contributor?
        </p>
        """, unsafe_allow_html=True)
    
    # Create tabs for audio and text input
    tab1, tab2 = st.tabs(["🎤 Record Audio", "⌨️ Type Response"])
    
    with tab1:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Click the microphone button below to record your response. Your audio will be transcribed automatically.
            </p>
            """, unsafe_allow_html=True)
        transcript = record_audio("collaboration_description", min_duration=10, max_duration=300)
    
    with tab2:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Type your response in the text box below.
            </p>
            """, unsafe_allow_html=True)
        text_response = st.text_area(
            "Your response:",
            key="collaboration_description_text",
            value=previous_collaboration_description,
            height=150,
            placeholder="Type your answer here...",
            label_visibility="collapsed"
        )
    
    # Use whichever response is available
    if transcript:
        collaboration_description = transcript
    elif text_response and text_response.strip():
        collaboration_description = text_response
    else:
        collaboration_description = previous_collaboration_description
    
    # Validation function
    def validate():
        return (all(response != "Not selected" for response in responses.values()) and 
                collaboration_description.strip() != "")
    
    def handle_back():
        save_and_navigate('back', collaboration_responses=responses, collaboration_description=collaboration_description)

    def handle_next():
        if not validate():
            return
        st.session_state['survey_responses']['collaboration_responses'] = responses
        st.session_state['survey_responses']['collaboration_description'] = collaboration_description

        participant_id = st.session_state['survey_responses'].get('participant_id')
        pr_number = st.session_state['survey_responses'].get('pr_number', 'N/A')
        pr_title = st.session_state['survey_responses'].get('pr_title', 'N/A')
        pr_url = st.session_state['survey_responses'].get('pr_url', 'N/A')

        if participant_id and pr_number != 'N/A':
            with st.spinner('Saving your responses...'):
                result = save_post_pr_closed_responses(
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
    navigation_buttons(
        on_back=handle_back,
        on_next=handle_next,
        back_key="collaboration_back",
        next_key="collaboration_next",
        validation_fn=validate,
        validation_error="Please answer all questions before proceeding."
    )
