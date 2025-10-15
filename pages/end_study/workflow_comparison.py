"""
End of study page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, navigation_buttons
from survey_utils import save_and_navigate


def workflow_comparison_page():
    """Display the end of study page."""
    page_header(
        "End of PR Reviews",
        "Thank you for reviewing the PRs and providing your feedback."
    )
    
    st.markdown("""
        <p style='font-size:18px; margin-bottom: 2rem;'>
        You have completed all the PR reviews. On the next page, we'll ask you to reflect on your experience in this study.
        </p>
        """, unsafe_allow_html=True)
    
    # Navigation
    navigation_buttons(
        on_back=lambda: save_and_navigate('back'),
        on_next=lambda: save_and_navigate('next'),
        back_key="workflow_back",
        next_key="workflow_next"
    )
