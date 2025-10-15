"""
Closure confirmation page.
Asks the reviewer to indicate if the PR has been closed or merged,
then routes to the post-PR-closed question pages.
"""

import streamlit as st
from survey_components import page_header, selectbox_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context
from survey_data import (
    get_repository_assignment,
    get_assigned_pr_for_reviewer,
    get_random_unassigned_pr,
    assign_pr_to_reviewer,
    update_contributor_repo_issues_status
)


def closure_confirmation_page():
    """Display the PR closure confirmation page."""
    page_header(
        "PR Closure",
        "Please indicate whether the PR has been closed or merged."
    )

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

    previous = st.session_state['survey_responses'].get('pr_closed_confirm', 'Not selected')
    selection = selectbox_question(
        "Has the PR been closed or merged?",
        ["Not yet", "Closed", "Merged"],
        "pr_closed_confirm",
        previous,
        placeholder="Select one"
    )

    if selection == "Closed" or selection == "Merged":
        issue_id = st.session_state['survey_responses'].get('issue_id')
        is_closed = selection == "Closed"
        is_merged = selection == "Merged"
        is_reviewed = True  # or set appropriately from the workflow logic
        result = update_contributor_repo_issues_status(issue_id, is_closed, is_merged, is_reviewed)
        if not result['success']:
            st.warning(f"Error updating contributor DB: {result['error']}")

    # Actions row: Assign another PR (wider, left), Continue (right-aligned)
    st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
    col_assign, col_spacer, col_continue = st.columns([4, 2.5, 1.5])

    # Track assignment result to display messages outside column
    assignment_error = None
    
    with col_assign:
        if participant_id and assigned_repo:
            if st.button("Assign me another PR from this repo", key="assign_another_pr"):
                with st.spinner('Looking for another PR in this repository...'):
                    pr_result = get_random_unassigned_pr(assigned_repo)
                    if pr_result['success'] and pr_result['pr']:
                        pr_data = pr_result['pr']
                        assign_result = assign_pr_to_reviewer(participant_id, pr_data['issue_id'])
                        if assign_result['success']:
                            st.session_state['survey_responses']['assigned_pr'] = pr_data
                            st.session_state['survey_responses']['pr_url'] = pr_data['url']
                            st.session_state['survey_responses']['issue_url'] = pr_data['issue_url']
                            st.session_state['survey_responses']['issue_id'] = pr_data['issue_id']
                            st.session_state['survey_responses']['reviewer_estimate'] = 'Not selected'
                            st.session_state['page'] = 4  # review_submission_page
                            st.rerun()
                        else:
                            assignment_error = f"⚠️ Error assigning PR: {assign_result['error']}"
                    else:
                        assignment_error = f"⚠️ {pr_result['error'] or 'No unassigned PRs available in this repo.'}"
    def validate():
        return selection in ("Closed", "Merged")

    def handle_next():
        if not validate():
            return
        st.session_state['survey_responses']['pr_closed_confirm'] = selection
        save_and_navigate('next', pr_closed_confirm=selection)

    with col_continue:
        if validate():
            if st.button("Continue", key="closure_confirmation_next"):
                handle_next()
    
    # Display assignment error outside columns for full width
    if assignment_error:
        st.error(assignment_error)


