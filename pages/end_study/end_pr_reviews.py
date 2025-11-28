"""
End-of-PR summary page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, navigation_buttons
from survey_utils import save_and_navigate


def end_pr_reviews_page():
    """Display the end of PR reviews summary page."""
    page_header(
        "End of PR Reviews",
        "Thank you for reviewing the PRs and providing your feedback."
    )
    
    st.markdown("""
        <p style='font-size:18px; margin-bottom: 2rem;'>
        You have reviewed all the PRs assigned to you. On the next page, we'll ask you to reflect on your experience in this study.
        </p>
        """, unsafe_allow_html=True)
    
    # Navigation (no back button)
    navigation_buttons(
        on_next=lambda: save_and_navigate('next'),
        next_key="end_pr_reviews_next",
        next_label="Next",
        show_back=False
    )
