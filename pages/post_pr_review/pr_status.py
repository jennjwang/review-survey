"""
PR status page to capture whether the assigned PR is closed or merged.
"""

import streamlit as st
from survey_components import page_header, selectbox_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context
from survey_data import get_assigned_pr_for_reviewer, get_repository_assignment, list_assigned_prs_for_reviewer


STATUS_OPTIONS = [
    "Not selected",
    "Not yet closed",
    "Closed",
    "Merged"
]


def pr_status_page():
    """Display the PR status page."""
    page_header(
        "PR Status",
        "Thanks for submitting your first review! Let us know if a PR is closed or merged."
    )

    # Load all PRs assigned to this reviewer; allow status update for any
    participant_id = st.session_state['survey_responses'].get('participant_id')
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository')
    if participant_id and not assigned_repo:
        repo_result = get_repository_assignment(participant_id)
        if repo_result['success']:
            assigned_repo = repo_result['repository']
            st.session_state['survey_responses']['assigned_repository'] = assigned_repo
            st.session_state['survey_responses']['repository_url'] = repo_result['url']

    pr = None
    pr_url = st.session_state['survey_responses'].get('pr_url')
    issue_url = st.session_state['survey_responses'].get('issue_url')
    pr_choices = []
    if participant_id and assigned_repo:
        assigned = list_assigned_prs_for_reviewer(participant_id, assigned_repo)
        if assigned['success'] and assigned['prs']:
            pr_choices = assigned['prs']
            labels = [f"PR {p['number']} - {p['issue_url']}" if p['number'] != 'N/A' else p['issue_url'] for p in pr_choices]
            selected_label = st.selectbox("Select a PR to update:", labels, index=0)
            idx = labels.index(selected_label)
            pr = pr_choices[idx]
            pr_url = pr['url']
            issue_url = pr['issue_url']
            st.session_state['survey_responses']['pr_url'] = pr_url
            st.session_state['survey_responses']['issue_url'] = issue_url

    display_pr_context(pr_url=pr_url, issue_url=issue_url)

    previous_value = st.session_state['survey_responses'].get('pr_status', 'Not selected')

    pr_status = selectbox_question(
        "What is the current status of this PR?",
        STATUS_OPTIONS,
        "pr_status",
        previous_value,
        placeholder="Select status"
    )

    def validate():
        return pr_status != "Not selected"

    def handle_next():
        if not validate():
            return
        st.session_state['survey_responses']['pr_status'] = pr_status
        # Optionally persist to a reviewer-pr-status table if present
        try:
            supabase = st.session_state.get('supabase_client')
            if not supabase:
                from survey_data import supabase_client as supabase
            if supabase and pr_url:
                payload = {
                    'participant_id': participant_id,
                    'pr_url': pr_url,
                    'issue_url': issue_url,
                    'status': pr_status,
                }
                try:
                    supabase.table('reviewer-pr-status').insert(payload).execute()
                except Exception:
                    pass
        except Exception:
            pass
        save_and_navigate('next', pr_status=pr_status)

    navigation_buttons(
        on_back=lambda: save_and_navigate('back', pr_status=pr_status),
        on_next=handle_next,
        back_key="pr_status_back",
        next_key="pr_status_next",
        validation_fn=validate,
        validation_error="Please select a PR status before proceeding."
    )


