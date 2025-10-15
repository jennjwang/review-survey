"""
Contributor perception page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, slider_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context, record_audio
from survey_data import save_post_pr_closed_responses
from survey_questions import PERCEPTION_QUESTIONS

# Perception slider options (1-5 with labels)
PERCEPTION_OPTIONS = ["Not selected", "1 - Strongly disagree", "2", "3", "4", "5 - Strongly agree"]


def contributor_perception_page():
    """Display the contributor perception page."""
    page_header(
        "Contributor Perception"
    )
    
    # Display PR context if available
    pr_url = st.session_state['survey_responses'].get('pr_url')
    issue_url = st.session_state['survey_responses'].get('issue_url')
    display_pr_context(pr_url=pr_url, issue_url=issue_url)
    
    st.markdown("""
        <p style='font-size:18px; font-weight: 600; margin-bottom: 2rem'>
        For each of the following traits, rate how strongly you agree that this describes the contributor after the discussion:
        </p>
        """, unsafe_allow_html=True)
    
    # Load previous responses
    previous_responses = st.session_state['survey_responses'].get('perception_responses', {})
    previous_perception_description = st.session_state['survey_responses'].get('perception_description', '')
    
    # Contributor perception rating questions
    responses = {}
    for key, question in PERCEPTION_QUESTIONS.items():
        previous_value = previous_responses.get(key, "Not selected")
        
        response = slider_question(
            question,
            PERCEPTION_OPTIONS,
            f"perception_{key}",
            previous_value
        )
        
        responses[key] = response
    
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    # Open-ended perception question with audio or text option
    st.markdown("""
        <p style='font-size:18px; font-weight:600; margin-bottom: 1.5rem;'>
        How did this PR discussion affect your perception of this contributor?
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
        transcript = record_audio("perception_description", min_duration=10, max_duration=300)
    
    with tab2:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Type your response in the text box below.
            </p>
            """, unsafe_allow_html=True)
        text_response = st.text_area(
            "Your response:",
            key="perception_description_text",
            value=previous_perception_description,
            height=150,
            placeholder="Type your answer here...",
            label_visibility="collapsed"
        )
    
    # Use whichever response is available
    if transcript:
        perception_description = transcript
    elif text_response and text_response.strip():
        perception_description = text_response
    else:
        perception_description = previous_perception_description
    
    # Validation function
    def validate():
        return (all(response != "Not selected" for response in responses.values()) and 
                perception_description.strip() != "")
    
    def handle_back():
        save_and_navigate('back', perception_responses=responses, perception_description=perception_description)

    def handle_next():
        if not validate():
            return
        st.session_state['survey_responses']['perception_responses'] = responses
        st.session_state['survey_responses']['perception_description'] = perception_description

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
        back_key="perception_back",
        next_key="perception_next",
        validation_fn=validate,
        validation_error="Please answer all questions before proceeding."
    )
