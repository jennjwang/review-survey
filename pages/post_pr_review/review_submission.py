"""
Review submission confirmation page.
Asks the reviewer to confirm they have submitted their first PR review,
then routes to the post-PR-review question pages.
"""

import streamlit as st
from survey_components import page_header, selectbox_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context
from survey_data import get_repository_assignment, get_assigned_pr_for_reviewer, save_session_state, update_is_reviewed_for_issue


def review_submission_page():
    """Display the review submission confirmation page."""
    page_header(
        "Submit Initial Review",
        "Please confirm that you have submitted your initial review for the assigned PR."
    )

    # Load PR context if missing
    pr_url = st.session_state['survey_responses'].get('pr_url')
    issue_url = st.session_state['survey_responses'].get('issue_url')
    participant_id = st.session_state['survey_responses'].get('participant_id')
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository')

    if participant_id and not assigned_repo:
        repo_result = get_repository_assignment(participant_id)
        if repo_result['success']:
            assigned_repo = repo_result['repository']
            st.session_state['survey_responses']['assigned_repository'] = assigned_repo
            st.session_state['survey_responses']['repository_url'] = repo_result['url']

    if participant_id and assigned_repo and (not pr_url or not issue_url):
        fetched = get_assigned_pr_for_reviewer(participant_id, assigned_repo)
        if fetched['success'] and fetched['pr']:
            pr = fetched['pr']
            st.session_state['survey_responses']['assigned_pr'] = pr
            st.session_state['survey_responses']['pr_url'] = pr['url']
            st.session_state['survey_responses']['issue_url'] = pr['issue_url']
            pr_url = pr['url']
            issue_url = pr['issue_url']

    display_pr_context(pr_url=pr_url, issue_url=issue_url)

    previous = st.session_state['survey_responses'].get('first_review_submitted', 'Not selected')
    selection = selectbox_question(
        "Have you submitted your initial review for this PR?",
        ["Not yet", "Yes - I've submitted my review"],
        "first_review_submitted",
        previous,
        placeholder="Select one"
    )

    def validate():
        return selection == "Yes - I've submitted my review"

    # def handle_next():
    #     if not validate():
    #         return
    #     st.session_state['survey_responses']['first_review_submitted'] = selection
    #     # Jump directly to the Post-PR-Review question flow (NASA-TLX start index)
    #     next_index = 6  # nasa_tlx_questions_page index in main routing
    #     participant = st.session_state['survey_responses'].get('participant_id')
    #     if participant:
    #         save_session_state(participant, next_index, st.session_state['survey_responses'])
    #     st.session_state['page'] = next_index
    #     st.rerun()
    def handle_next():
        if not validate():
            return
        st.session_state['survey_responses']['first_review_submitted'] = selection
        # ---- Add this block ----
        issue_id = st.session_state['survey_responses'].get('issue_id')
        if issue_id:
            result = update_is_reviewed_for_issue(issue_id, True)
            if not result['success']:
                st.warning(f"Error updating contributor DB: {result['error']}")
        # Jump directly to the Post-PR-Review question flow (NASA-TLX start index)
        next_index = 6  # nasa_tlx_questions_page index
        participant = st.session_state['survey_responses'].get('participant_id')
        if participant:
            save_session_state(participant, next_index, st.session_state['survey_responses'])
        st.session_state['page'] = next_index
        st.rerun()

    navigation_buttons(
        on_back=lambda: save_and_navigate('back', first_review_submitted=selection),
        on_next=handle_next,
        back_key="review_submission_back",
        next_key="review_submission_next",
        validation_fn=validate,
        validation_error="Please keep working on your first review before proceeding!"
    )


