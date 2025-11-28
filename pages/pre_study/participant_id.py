"""
Review email page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, text_input_question, navigation_buttons
from survey_utils import save_and_navigate
from survey_data import validate_participant_id, get_repository_assignment, determine_current_page


def participant_id_page():
    """Display the email page."""
    page_header(
        "Reviewer Information"
    )
    
    # Load previous response if exists
    previous_participant_id = st.session_state['survey_responses'].get('participant_id', '')
    
    # email input
    participant_id = text_input_question(
        "Please enter your email to begin the survey:",
        "participant_id",
        previous_participant_id,
        placeholder="Enter your email"
    )
    
    # Show repository assignment if email is valid
    assigned_repo = None
    if participant_id and participant_id.strip():
        try:
            # Validate email
            validation_result = validate_participant_id(participant_id)
            
            if validation_result['valid']:
                # st.success(f"email '{participant_id}' validated successfully!")
                # Persist participant_id immediately so downstream pages can use it
                st.session_state['survey_responses']['participant_id'] = participant_id

                # Determine the correct page based on completion status
                correct_page = determine_current_page(participant_id, st.session_state['survey_responses'])
                if correct_page > 0:
                    st.session_state['page'] = correct_page
                    st.rerun()

                # Get repository assignment
                repo_result = get_repository_assignment(participant_id)
                
                if repo_result['success']:
                    assigned_repo = repo_result['repository']
                    repository_url = repo_result['url']
                    st.session_state['survey_responses']['assigned_repository'] = assigned_repo
                    st.session_state['survey_responses']['repository_url'] = repository_url
                    st.info(f"**Assigned Repository:** {assigned_repo}")
                else:
                    st.error(f"⚠️ {repo_result['error']}")
                    assigned_repo = None
                    # Clear any stale assignment from session state
                    st.session_state['survey_responses'].pop('assigned_repository', None)
                    st.session_state['survey_responses'].pop('repository_url', None)
            else:
                st.error(f"⚠️ {validation_result['error']}")
                assigned_repo = None
                # Clear any stale assignment from session state
                st.session_state['survey_responses'].pop('assigned_repository', None)
                st.session_state['survey_responses'].pop('repository_url', None)
        except Exception as e:
            st.error(f"Error validating email: {str(e)}")
            assigned_repo = None
            # Clear any stale assignment from session state
            st.session_state['survey_responses'].pop('assigned_repository', None)
            st.session_state['survey_responses'].pop('repository_url', None)
    
    # Validation function
    def validate():
        # Only allow Next if the current validation flow assigned a repository
        return participant_id and participant_id.strip() != "" and assigned_repo is not None
    
    # Navigation
    navigation_buttons(
        on_back=lambda: save_and_navigate('back', participant_id=participant_id),
        on_next=lambda: save_and_navigate('next', participant_id=participant_id),
        back_key="participant_id_back",
        next_key="participant_id_next",
        show_back=False,
        validation_fn=validate,
        validation_error="Please enter a valid email before proceeding."
    )
