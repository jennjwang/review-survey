"""
PR status page to capture whether the assigned PR is closed or merged.
"""

import streamlit as st
from survey_components import page_header, selectbox_question, navigation_buttons
from survey_utils import save_and_navigate
from survey_data import (
    get_repository_assignment, 
    list_assigned_prs_for_reviewer, 
    update_contributor_repo_issues_status,
    get_random_unassigned_pr,
    assign_pr_to_reviewer
)


STATUS_OPTIONS = [
    "Not selected",
    "Still open - review in progress",
    "Merged - PR was accepted and merged",
    "Closed without merging - PR was rejected or abandoned"
]


def pr_status_page():
    """Display the PR status page."""
    st.header("PR Review Status")
    st.markdown("""
        <p style='font-size:18px; font-weight: 400; margin-bottom: 2rem'>
        Thank you for reviewing the assigned PR! <br>
        Please update the status of your assigned PR below once it has been merged or closed. 
        If you would like to review a different PR instead, you can request another PR below.
        </p>
        """, unsafe_allow_html=True)

    # Load all PRs assigned to this reviewer; allow status update for any
    participant_id = st.session_state['survey_responses'].get('participant_id')
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository')
    if participant_id and not assigned_repo:
        repo_result = get_repository_assignment(participant_id)
        if repo_result['success']:
            assigned_repo = repo_result['repository']
            st.session_state['survey_responses']['assigned_repository'] = assigned_repo
            st.session_state['survey_responses']['repository_url'] = repo_result['url']

    pr_url = st.session_state['survey_responses'].get('pr_url')
    
    if participant_id and assigned_repo:
        assigned = list_assigned_prs_for_reviewer(participant_id, assigned_repo)
        if assigned['success'] and assigned['prs']:
            pr_choices = assigned['prs']
            labels = [f"PR #{p['number']}: {p['url']}" if p['number'] != 'N/A' else p['title'] for p in pr_choices]

            st.markdown(
                "<p style='font-size:18px; font-weight: 400; margin-bottom:0.5rem;'>Select a PR</p>", 
                unsafe_allow_html=True
            )
            selected_label = st.selectbox("", labels, index=0, label_visibility="collapsed")

            idx = labels.index(selected_label)
            pr = pr_choices[idx]
            pr_url = pr['url']
            st.session_state['survey_responses']['pr_url'] = pr_url
            st.session_state['survey_responses']['issue_id'] = pr.get('issue_id')

    if pr_url:
        st.info(f"**Link to PR:** [{pr_url}]({pr_url})")
    else:
        st.warning("⚠️ No PR assigned yet.")

    st.divider()

    previous_value = st.session_state['survey_responses'].get('pr_status', 'Not selected')

    pr_status = selectbox_question(
        "What is the current status of this PR?",
        STATUS_OPTIONS,
        "pr_status",
        previous_value,
        placeholder="Select the PR status"
    )
    
    st.markdown("")

    # Show info box if PR is still in progress
    if pr_status == "Still open - review in progress":
        st.info("""
        - Please continue collaborating with the contributor until the PR is ready to merge.
        - If there's no response for 2+ weeks, you may close the PR as abandoned.
        - Return here to update the status once the PR is merged or closed.""")

    def validate():
        return pr_status != "Not selected"

    def handle_next():
        if not validate():
            return
        st.session_state['survey_responses']['pr_status'] = pr_status
        
        # Update is_merged/is_closed in the contributor database
        issue_id = st.session_state['survey_responses'].get('issue_id')
        if issue_id:
            is_merged = pr_status == "Merged - PR was accepted and merged"
            is_closed = pr_status == "Closed without merging - PR was rejected or abandoned"
            if is_merged or is_closed:
                result = update_contributor_repo_issues_status(issue_id, is_closed, is_merged, True)
                if not result['success']:
                    st.warning(f"Error updating PR status: {result['error']}")
        
        # If PR is closed or merged, proceed to post-PR-closed questions
        if pr_status in ["Merged - PR was accepted and merged", "Closed without merging - PR was rejected or abandoned"]:
            save_and_navigate('next', pr_status=pr_status)
        else:
            # PR still open - stay on this page
            st.session_state['survey_responses']['pr_status'] = pr_status

    # Actions row: Assign another PR (left), Continue (right)
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    
    assignment_error = None
    
    col_assign, col_spacer, col_continue = st.columns([4, 2.5, 1.5])
    
    with col_assign:
        if participant_id and assigned_repo:
            if st.button("Request another PR", key="assign_another_pr", use_container_width=True):
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
                            st.session_state['survey_responses']['pr_status'] = 'Not selected'
                            st.session_state['page'] = 4  # review_submission_page
                            st.rerun()
                        else:
                            assignment_error = f"⚠️ Error assigning PR: {assign_result['error']}"
                    else:
                        assignment_error = f"⚠️ {pr_result.get('error') or 'No unassigned PRs available in this repo.'}"

    with col_continue:
        if pr_status in ["Merged - PR was accepted and merged", "Closed without merging - PR was rejected or abandoned"]:
            if st.button("Continue", key="pr_status_next", type="primary", use_container_width=True):
                handle_next()
    
    # Display assignment error outside columns for full width
    if assignment_error:
        st.error(assignment_error)


