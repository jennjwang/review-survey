"""
NASA-TLX questions page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, slider_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context
from survey_questions import NASA_TLX_QUESTIONS
from survey_data import save_post_pr_review_responses

# NASA-TLX slider options (1-7 with labels)
NASA_TLX_OPTIONS = ["Not selected", "1 - Very low", "2", "3", "4", "5", "6", "7 - Very high"]


def nasa_tlx_questions_page():
    """Display the NASA-TLX questions page."""
    page_header(
        "PR Review Experience",
        "Please rate your experience while reviewing this PR."
    )
    
    # Display PR context if available
    pr_url = st.session_state['survey_responses'].get('pr_url')
    issue_url = st.session_state['survey_responses'].get('issue_url')
    display_pr_context(pr_url=pr_url)
    
    # st.markdown("""
    #     <p style='font-size:18px; font-weight: 600; margin-bottom: 2rem'>
    #     Please rate the following aspects of your review experience:
    #     </p>
    #     """, unsafe_allow_html=True)
    
    # Load previous responses
    previous_responses = st.session_state['survey_responses'].get('nasa_tlx_responses', {})
    
    # NASA-TLX questions
    responses = {}
    for key, question in NASA_TLX_QUESTIONS.items():
        previous_value = previous_responses.get(key, "Not selected")
        
        response = slider_question(
            question,
            NASA_TLX_OPTIONS,
            f"nasa_tlx_{key}",
            previous_value
        )
        
        responses[key] = response
    
    # Validation function
    def validate():
        return all(response != "Not selected" for response in responses.values())
    
    # Custom navigation handlers with data saving
    def handle_back():
        save_and_navigate('back', nasa_tlx_responses=responses)
    
    def handle_next():
        if not validate():
            return
        
        # Save to session state and continue. We persist to DB on the last page of this section.
        st.session_state['survey_responses']['nasa_tlx_responses'] = responses
        save_and_navigate('next', nasa_tlx_responses=responses)
    
    # Navigation
    navigation_buttons(
        on_back=handle_back,
        on_next=handle_next,
        back_key="nasa_tlx_back",
        next_key="nasa_tlx_next",
        validation_fn=validate,
        validation_error="Please answer all questions before proceeding."
    )
