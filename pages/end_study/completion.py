"""
Survey completion page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, navigation_buttons
from survey_utils import next_page
from survey_data import (
    save_session_state, get_repository_assignment, list_assigned_prs_for_reviewer,
    get_completed_pr_closed_surveys,
)


def completion_page():
    """Display the survey completion page."""
    participant_id = st.session_state['survey_responses'].get('participant_id')
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository')

    if participant_id and not assigned_repo:
        repo_result = get_repository_assignment(participant_id)
        if repo_result['success']:
            assigned_repo = repo_result['repository']
            st.session_state['survey_responses']['assigned_repository'] = assigned_repo
            st.session_state['survey_responses']['repository_url'] = repo_result['url']

    if participant_id and assigned_repo:
        assigned = list_assigned_prs_for_reviewer(participant_id, assigned_repo)
        if assigned.get('success'):
            all_prs = assigned.get('prs', [])

            open_prs = [pr for pr in all_prs if not pr.get('is_closed') and not pr.get('is_merged')]
            if open_prs:
                st.warning("You still have PRs to review or close. Redirecting to PR Status.")
                st.session_state['page'] = 8
                st.rerun()
                return

            # Also check for closed/merged PRs that are missing post-pr-closed surveys
            _norm = lambda u: (u or '').strip().rstrip('/')
            closed_survey_urls = {_norm(u) for u in get_completed_pr_closed_surveys(participant_id)}
            pending_closed = [
                pr for pr in all_prs
                if pr.get('is_reviewed') and (pr.get('is_closed') or pr.get('is_merged'))
                and _norm(pr.get('url', '')) not in closed_survey_urls
            ]
            if pending_closed:
                st.warning(
                    f"You have {len(pending_closed)} closed PR(s) with missing survey responses. "
                    "Redirecting to PR Status."
                )
                st.session_state['page'] = 8
                st.rerun()
                return

    page_header(
        "Survey Completed!",
    )
    
    st.markdown("""
        <p style='font-size:20px'>
        Thank you for participating in our research study.
        </p>
        """, unsafe_allow_html=True)
    
    # # Display summary of responses
    # with st.expander("View your responses"):
    #     st.json(st.session_state['survey_responses'])
    
    # Mark session as completed
    participant_id = st.session_state['survey_responses'].get('participant_id')
    if participant_id:
        try:
            from datetime import datetime, timezone
            # Save final page and completed_at
            save_session_state(participant_id, st.session_state.get('page', 12), st.session_state['survey_responses'])
            # Directly update completed_at
            supabase = st.session_state.get('supabase_client')
            # Fallback to module-level client if not in session
            if not supabase:
                from survey_data import supabase_client as supabase
            if supabase:
                supabase.table('reviewer-sessions').update({
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }).eq('participant_id', participant_id).execute()
        except Exception:
            pass

    st.markdown("""
        <p style='font-size:16px; margin-bottom: 1rem;'>
        If you have any questions or concerns,
        please contact jennjwang@stanford.edu.
        </p>
        """, unsafe_allow_html=True)
