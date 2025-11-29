"""
Participant ID page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, text_input_question
from survey_data import validate_participant_id, get_participant_progress, get_repository_assignment


def participant_id_page():
    """Display the participant ID input page."""
    page_header(
        "The Ripple Effects of AI in Software Development",
        "Please enter your email to begin the survey."
    )

    # Load previous participant ID if it exists
    previous_participant_id = st.session_state['survey_responses'].get('participant_id', '')

    # Participant ID input
    participant_id = text_input_question(
        "Email:",
        "participant_id_input",
        previous_participant_id,
        placeholder="Enter your email"
    )

    # Navigation - hide back button since this is the first page
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    next_clicked = st.button("Next", key="participant_id_next")

    if next_clicked:
        # Basic validation first
        if not participant_id or not participant_id.strip():
            st.error("Please enter your email to proceed.")
        else:
            # Validate against database
            with st.spinner('Validating email...'):
                validation_result = validate_participant_id(participant_id)

            if validation_result['valid']:
                # ID is valid, save it
                st.session_state['survey_responses']['participant_id'] = participant_id

                # Get repository assignment
                with st.spinner('Loading your assignment...'):
                    repo_result = get_repository_assignment(participant_id)

                if repo_result['success']:
                    assigned_repo = repo_result['repository']
                    repository_url = repo_result['url']
                    st.session_state['survey_responses']['assigned_repository'] = assigned_repo
                    st.session_state['survey_responses']['repository_url'] = repository_url

                # Check progress to see if they should skip ahead
                with st.spinner('Checking your progress...'):
                    progress_result = get_participant_progress(participant_id)

                if progress_result['success']:
                    progress = progress_result['progress']

                    # Check if they have started reviews
                    has_started_reviews = progress.get('post_pr_review_count', 0) > 0

                    if has_started_reviews:
                        # They've started, route to PR status page
                        st.info("Welcome back! You've already started reviewing.")
                        st.session_state['page'] = 8  # pr_status_page
                        st.rerun()
                    else:
                        # New reviewer, proceed to next page
                        st.session_state['page'] = 2  # setup_checklist_page
                        st.rerun()
                else:
                    # Couldn't check progress, just proceed normally
                    st.session_state['page'] = 2  # setup_checklist_page
                    st.rerun()
            else:
                # ID is not valid, show error
                st.error(f"{validation_result['error']}")
