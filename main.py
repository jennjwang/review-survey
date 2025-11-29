"""
Main Streamlit application for the reviewer survey.
Organized into three main sections: Pre-study, Post-PR-Review, and Post-PR-Closed.
"""

import streamlit as st
import streamlit.components.v1 as components
from styles import SURVEY_STYLES
from pages import (
    # Pre-study pages
    participant_id_page,
    setup_checklist_page,
    pr_assignment_page,

    # Post-PR-Review pages
    nasa_tlx_questions_page,
    code_quality_ratings_page,
    ai_detection_page,
    review_submission_page,

    # Post-PR-Closed pages
    pr_status_page,
    collaboration_questions_page,
    contributor_perception_page,

    # End of study pages
    study_validation_page,

    # Completion pages
    completion_page
)
from survey_utils import normalize_page


def initialize_session_state():
    """Initialize session state variables."""
    if 'page' not in st.session_state:
        st.session_state['page'] = 0

    if 'survey_responses' not in st.session_state:
        st.session_state['survey_responses'] = {}


def main():
    """Main application entry point."""
    st.set_page_config(page_title="Reviewer Survey", layout="centered")

    # Apply custom CSS styles
    st.markdown(SURVEY_STYLES, unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Smart routing: determine correct page based on data before rendering
    # Only run once at the start of the session, not on every page interaction
    if not st.session_state.get('smart_routing_complete', False):
        participant_id = st.session_state['survey_responses'].get('participant_id')
        if participant_id and st.session_state.get('page', 0) != 0:
            from survey_data import determine_current_page
            correct_page = determine_current_page(participant_id, st.session_state['survey_responses'])
            current_page = st.session_state.get('page', 0)

            # Only update if the determined page is different from current page
            if correct_page != current_page:
                print(f"[ROUTING] Current page: {current_page}, Correct page: {correct_page}, redirecting...")
                st.session_state['page'] = correct_page
                st.session_state['smart_routing_complete'] = True
                st.rerun()
            else:
                st.session_state['smart_routing_complete'] = True

    # Route to the appropriate page based on session state
    # Flow: Pre-study → Post-PR-Review questions → PR Status → Post-PR-Closed questions → End-Study
    page_routes = {
        # Pre-study section
        0: participant_id_page,             # Participant ID entry
        2: setup_checklist_page,            # Setup checklist
        3: pr_assignment_page,              # PR assignment
        4: review_submission_page,          # Confirm first review submitted

        # Post-PR-Review section (questions about the review experience)
        5: nasa_tlx_questions_page,         # NASA-TLX workload questions
        6: code_quality_ratings_page,       # Code quality ratings
        7: ai_detection_page,               # AI detection questions

        # PR Status check (after questions, check if PR is closed/merged)
        8: pr_status_page,                  # PR status - can request another PR here

        # Post-PR-Closed section (only if PR is closed/merged)
        9: collaboration_questions_page,    # Collaboration questions
        10: contributor_perception_page,    # Contributor perception questions

        # End of study section
        11: study_validation_page,          # Study validation

        # Completion section
        12: completion_page                 # Survey completion
    }
    
    current_page = st.session_state.get('page', 0)
    normalized_page = normalize_page(current_page)
    if normalized_page != current_page:
        st.session_state['page'] = normalized_page
        current_page = normalized_page
    page_function = page_routes.get(current_page, participant_id_page)
    page_function()


if __name__ == "__main__":
    main()
