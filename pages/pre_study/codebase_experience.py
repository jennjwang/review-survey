"""
Codebase experience page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, selectbox_question, navigation_buttons
from survey_utils import save_and_navigate
from survey_questions import CODEBASE_EXPERIENCE_OPTIONS
from survey_data import save_pre_study_responses


def codebase_experience_page():
    """Display the codebase experience page."""
    page_header(
        "Codebase Familiarity",
        "Tell us about your experience with the codebase you'll be reviewing."
    )
    
    # Display codebase information if available
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository', 'N/A')
    repository_url = st.session_state['survey_responses'].get('repository_url', 'N/A')
    
    if assigned_repo != 'N/A':
        st.info(f"""
        **Codebase you'll be reviewing:**
        - **Repository:** {assigned_repo}
        - **URL:** {repository_url}
        """)
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ No codebase assignment found. Please complete the participant ID step first.")
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Load previous response
    previous_codebase_exp = st.session_state['survey_responses'].get('codebase_experience', None)
    
    # Codebase experience question
    codebase_experience = selectbox_question(
        "How many lines of code, approximately, have you personally written or modified in this codebase?",
        CODEBASE_EXPERIENCE_OPTIONS,
        "codebase_experience",
        previous_codebase_exp
    )
    
    # Validation function
    def validate():
        return codebase_experience
    
    # Custom navigation handlers with data saving
    def handle_back():
        save_and_navigate('back', codebase_experience=codebase_experience)
    
    def handle_next():
        if not validate():
            return
        
        # Save to session state
        st.session_state['survey_responses']['codebase_experience'] = codebase_experience
        
        # Save to database
        participant_id = st.session_state['survey_responses'].get('participant_id')
        if participant_id:
            with st.spinner('Saving your responses...'):
                result = save_pre_study_responses(participant_id, st.session_state['survey_responses'])
            
            if result['success']:
                print(f"✅ Pre-study responses saved for participant {participant_id}")
                save_and_navigate('next', codebase_experience=codebase_experience)
            else:
                st.error(f"⚠️ Error saving responses: {result['error']}")
                print(f"Failed to save pre-study responses: {result['error']}")
        else:
            save_and_navigate('next', codebase_experience=codebase_experience)
    
    # Navigation
    navigation_buttons(
        on_back=handle_back,
        on_next=handle_next,
        back_key="codebase_exp_back",
        next_key="codebase_exp_next",
        validation_fn=validate,
        validation_error="Please select your codebase experience level to proceed."
    )
