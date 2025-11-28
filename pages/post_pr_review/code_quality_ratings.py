"""
Code quality ratings page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, slider_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context
from survey_questions import CODE_QUALITY_QUESTIONS
from survey_data import save_post_pr_review_responses, get_repository_assignment, get_assigned_pr_for_reviewer

# Code quality slider options (1-5 with labels)
CODE_QUALITY_OPTIONS = ["Not selected", "1 - Strongly disagree", "2", "3", "4", "5 - Strongly agree"]


def code_quality_ratings_page():
    """Display the code quality ratings page."""
    # Check if already completed - skip to next page
    participant_id = st.session_state['survey_responses'].get('participant_id')
    pr_url = st.session_state['survey_responses'].get('pr_url')

    if participant_id and pr_url:
        from survey_data import check_code_quality_completed
        if check_code_quality_completed(participant_id, pr_url):
            print(f"[CODE QUALITY] Already completed for {pr_url}, skipping to next page")
            st.session_state['page'] = st.session_state.get('page', 6) + 1
            st.rerun()
            return

    page_header(
        "Code Quality Assessment",
        "Please rate how much you agree with the following statements about the code in this PR."
    )

    # Load PR context if missing
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository')
    
    # Load repository if missing
    if participant_id and not assigned_repo:
        repo_result = get_repository_assignment(participant_id)
        if repo_result['success']:
            assigned_repo = repo_result['repository']
            st.session_state['survey_responses']['assigned_repository'] = assigned_repo
    
    # Load PR if missing
    if participant_id and assigned_repo and not pr_url:
        fetched = get_assigned_pr_for_reviewer(participant_id, assigned_repo)
        if fetched['success'] and fetched['pr']:
            pr = fetched['pr']
            st.session_state['survey_responses']['pr_url'] = pr['url']
            st.session_state['survey_responses']['issue_url'] = pr.get('issue_url')
            st.session_state['survey_responses']['issue_id'] = pr.get('issue_id')
            pr_url = pr['url']
    
    display_pr_context(pr_url=pr_url)
    
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
    
    def handle_next():
        if not validate():
            return
        
        # Save to session state
        st.session_state['survey_responses']['code_quality_responses'] = responses
        
        # Save to database
        participant_id = st.session_state['survey_responses'].get('participant_id')
        pr_url = st.session_state['survey_responses'].get('pr_url', 'N/A')
        
        if participant_id:
            with st.spinner('Saving your responses...'):
                result = save_post_pr_review_responses(
                    participant_id,
                    pr_url,
                    st.session_state['survey_responses']
                )
            if not result.get('success'):
                st.error(f"⚠️ Error saving responses: {result.get('error')}")
                return
        
        save_and_navigate('next', code_quality_responses=responses)
    
    # Navigation
    navigation_buttons(
        on_back=lambda: save_and_navigate('back', code_quality_responses=responses),
        on_next=handle_next,
        back_key="code_quality_back",
        next_key="code_quality_next",
        validation_fn=validate,
        validation_error="Please answer all questions before proceeding."
    )
