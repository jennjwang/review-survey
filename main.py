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
    developer_experience_page,
    codebase_experience_page,
    pr_assignment_page,

    # Post-PR-Review pages
    nasa_tlx_questions_page,
    code_quality_ratings_page,
    ai_detection_page,
    pr_status_page,
    review_submission_page,

    # Post-PR-Closed pages
    collaboration_questions_page,
    contributor_perception_page,
    closure_confirmation_page,

    # End of study pages
    workflow_comparison_page,
    study_validation_page,

    # Completion pages
    completion_page
)


def initialize_session_state():
    """Initialize session state variables."""
    if 'page' not in st.session_state:
        st.session_state['page'] = 0
    
    if 'survey_responses' not in st.session_state:
        st.session_state['survey_responses'] = {}
    
    # Check if we should load existing session
    if 'session_loaded' not in st.session_state:
        participant_id = st.session_state['survey_responses'].get('participant_id')
        if participant_id:
            # Load existing session (import here to avoid circular dependency)
            from survey_data import load_session_state
            session_result = load_session_state(participant_id)
            if session_result['success'] and session_result['current_page'] > 0:
                st.session_state['page'] = session_result['current_page']
                st.session_state['survey_responses'].update(session_result['survey_responses'])
                st.info(f"🔄 Resumed session from page {session_result['current_page']}")
        st.session_state['session_loaded'] = True


def main():
    """Main application entry point."""
    st.set_page_config(page_title="Reviewer Survey", layout="centered")
    
    # Apply custom CSS styles
    st.markdown(SURVEY_STYLES, unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()
    
    # Route to the appropriate page based on session state
    # Organized by survey sections: Pre-study (0-3), Post-PR-Review (4-7), Post-PR-Closed (8-9), End-Study (10-11), Completion (12)
    page_routes = {
        # Pre-study section
        # 0: consent_page,                    # Consent form
        0: participant_id_page,             # Participant ID entry
        1: developer_experience_page,       # Professional experience
        2: codebase_experience_page,        # Codebase experience questions
        3: pr_assignment_page,              # PR assignment
        4: review_submission_page,          # Confirm first review submitted

        # Post-PR-Review section
        5: pr_status_page,                  # PR status (can be revisited later)
        6: nasa_tlx_questions_page,         # NASA-TLX workload questions
        7: code_quality_ratings_page,       # Code quality ratings
        8: ai_detection_page,               # AI detection questions

        # Post-PR-Closed section
        9: closure_confirmation_page,       # Confirm PR is closed/merged
        10: collaboration_questions_page,   # Collaboration questions
        11: contributor_perception_page,    # Contributor perception questions

        # End of study section
        12: workflow_comparison_page,       # Workflow comparison
        13: study_validation_page,          # Study validation

        # Completion section
        14: completion_page                 # Survey completion
    }
    
    current_page = st.session_state.get('page', 0)
    page_function = page_routes.get(current_page, participant_id_page)
    page_function()


if __name__ == "__main__":
    main()
