"""
Code quality ratings page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, slider_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context
from survey_questions import CODE_QUALITY_QUESTIONS

# Code quality slider options (1-5 with labels)
CODE_QUALITY_OPTIONS = ["Not selected", "1 - Strongly disagree", "2", "3", "4", "5 - Strongly agree"]


def code_quality_ratings_page():
    """Display the code quality ratings page."""
    page_header(
        "Code Quality Assessment",
        "Please rate how much you agree with the following statements about the code in this PR."
    )
    
    # Display PR context if available
    pr_url = st.session_state['survey_responses'].get('pr_url')
    issue_url = st.session_state['survey_responses'].get('issue_url')
    display_pr_context(pr_url=pr_url, issue_url=issue_url)
    
    # Load previous responses
    previous_responses = st.session_state['survey_responses'].get('code_quality_responses', {})
    
    # Code quality questions
    responses = {}
    for key, question in CODE_QUALITY_QUESTIONS.items():
        previous_value = previous_responses.get(key, "Not selected")
        
        response = slider_question(
            question,
            CODE_QUALITY_OPTIONS,
            f"code_quality_{key}",
            previous_value
        )
        
        responses[key] = response
    
    # Validation function
    def validate():
        return all(response != "Not selected" for response in responses.values())
    
    # Navigation
    navigation_buttons(
        on_back=lambda: save_and_navigate('back', code_quality_responses=responses),
        on_next=lambda: save_and_navigate('next', code_quality_responses=responses),
        back_key="code_quality_back",
        next_key="code_quality_next",
        validation_fn=validate,
        validation_error="Please answer all questions before proceeding."
    )
