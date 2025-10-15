"""
Study validation questions page (end-study).
Asks about how the study workflow compared to normal work.
"""

import streamlit as st
from survey_components import page_header, navigation_buttons
from survey_utils import save_and_navigate, record_audio
from survey_data import save_end_study_responses


def study_validation_page():
    """Display study validation questions about workflow comparison."""
    page_header(
        "Study Experience"
    )

    # Load previous responses
    previous_response = st.session_state['survey_responses'].get('workflow_comparison', '')

    # Question: Workflow comparison
    st.markdown("""
        <p style='font-size:18px; font-weight:600; margin-bottom: 1.5rem;'>
        How different did your workflow in this study feel compared to your normal day-to-day responsibilities? How did the PRs you reviewed during this study compare to the ones you usually handle?
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
        transcript = record_audio("workflow_comparison", min_duration=10, max_duration=300)

    with tab2:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Type your response in the text box below.
            </p>
            """, unsafe_allow_html=True)
        text_response = st.text_area(
            "Your response:",
            key="workflow_comparison_text",
            value=previous_response,
            height=200,
            placeholder="Type your answer here...",
            label_visibility="collapsed"
        )

    # Use whichever response is available
    if transcript:
        workflow_comparison = transcript
    elif text_response and text_response.strip():
        workflow_comparison = text_response
    else:
        workflow_comparison = previous_response

    # Validation function
    def validate():
        return workflow_comparison.strip() != ""

    def handle_back():
        save_and_navigate('back', workflow_comparison=workflow_comparison)

    def handle_next():
        if not validate():
            return
        st.session_state['survey_responses']['workflow_comparison'] = workflow_comparison
        participant_id = st.session_state['survey_responses'].get('participant_id')
        if participant_id:
            with st.spinner('Saving your response...'):
                result = save_end_study_responses(participant_id, st.session_state['survey_responses'])
            if not result.get('success'):
                st.error(f"⚠️ Error saving response: {result.get('error')}")
                return
        save_and_navigate('next')

    # Navigation
    navigation_buttons(
        on_back=handle_back,
        on_next=handle_next,
        back_key="study_validation_back",
        next_key="study_validation_next",
        validation_fn=validate,
        validation_error="Please provide a response before proceeding."
    )

