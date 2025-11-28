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
        "PR Review Status",
        "Let's check on your assigned PR."
    )

    # Load PR context if missing
    pr_url = st.session_state['survey_responses'].get('pr_url')
    issue_url = st.session_state['survey_responses'].get('issue_url')
    issue_id = st.session_state['survey_responses'].get('issue_id')
    participant_id = st.session_state['survey_responses'].get('participant_id')
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository')

    if participant_id and not assigned_repo:
        repo_result = get_repository_assignment(participant_id)
        if repo_result['success']:
            assigned_repo = repo_result['repository']
            st.session_state['survey_responses']['assigned_repository'] = assigned_repo
            st.session_state['survey_responses']['repository_url'] = repo_result['url']

    if participant_id and assigned_repo and (not pr_url or not issue_url or not issue_id):
        fetched = get_assigned_pr_for_reviewer(participant_id, assigned_repo)
        if fetched['success'] and fetched['pr']:
            pr = fetched['pr']
            st.session_state['survey_responses']['assigned_pr'] = pr
            st.session_state['survey_responses']['pr_url'] = pr['url']
            st.session_state['survey_responses']['issue_url'] = pr['issue_url']
            st.session_state['survey_responses']['issue_id'] = pr['issue_id']
            pr_url = pr['url']
            issue_url = pr['issue_url']

    # Display PR info in a styled box
    st.info(f"""
    **PR:** {pr_url if pr_url else 'N/A'}
    """)

    st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)

    # Main question section
    st.markdown("### Have you completed your initial review?")
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    st.markdown("Please confirm that you have:")
    st.markdown("""
    - Reviewed the PR thoroughly
    - Provided feedback on the code
    """)

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # Get previous selection
    previous = st.session_state['survey_responses'].get('is_reviewed', None)

    # Create two-column layout for buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Yes, I've completed my review", key="review_yes", use_container_width=True, type="primary"):
            # Save response
            st.session_state['survey_responses']['is_reviewed'] = "Yes - I've submitted my review"

            # Update is_reviewed flag in database
            issue_id = st.session_state['survey_responses'].get('issue_id')
            print(f"[DEBUG] Updating is_reviewed for issue_id={issue_id}")
            if issue_id:
                result = update_is_reviewed_for_issue(issue_id, True)
                print(f"[DEBUG] update_is_reviewed_for_issue result: {result}")
                if not result['success']:
                    st.warning(f"Error updating contributor DB: {result['error']}")
            else:
                print("[DEBUG] No issue_id found in session state!")
                st.warning("Could not update review status: missing issue_id")

            # Navigate to next page
            next_index = 5  # pr_status_page index
            participant = st.session_state['survey_responses'].get('participant_id')
            if participant:
                save_session_state(participant, next_index, st.session_state['survey_responses'])
            st.session_state['page'] = next_index
            st.rerun()

    with col2:
        if st.button("Not yet, still working on it", key="review_no", use_container_width=True):
            st.session_state['survey_responses']['is_reviewed'] = "Not yet"
            st.info("Please complete your initial review before proceeding.")

