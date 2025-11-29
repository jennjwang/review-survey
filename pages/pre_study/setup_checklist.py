"""
Reviewer setup checklist page.
"""

import streamlit as st
from survey_components import page_header, navigation_buttons
from survey_utils import save_and_navigate, extract_repo_url
from survey_data import get_repository_assignment, get_participant_progress, list_assigned_prs_for_reviewer


CHECKLIST_KEYS = {
    'invitation_accepted': "Please accept the invite to the swe-productivity fork of your repository",
    'recorder_ready': "Install the [recording tool](https://github.com/jennjwang/swe-prod-recorder) and confirm that it works properly"
}


def setup_checklist_page():
    """Display the reviewer setup checklist page."""
    responses = st.session_state['survey_responses']
    participant_id = responses.get('participant_id')

    # Check if reviewer has already started (has completed at least one review OR has an assigned PR)
    if participant_id:
        progress_result = get_participant_progress(participant_id)
        if progress_result.get('success') and progress_result.get('progress'):
            # If they already have completed a review, skip the checklist
            if progress_result['progress'].get('post_pr_review_count', 0) > 0:
                st.session_state['page'] += 1
                st.rerun()
                return

        # Also check if they have any assigned PRs
        repo_result = get_repository_assignment(participant_id)
        if repo_result.get('success') and repo_result.get('repository'):
            assigned_repo = repo_result['repository']
            prs_result = list_assigned_prs_for_reviewer(participant_id, assigned_repo)
            if prs_result.get('success') and prs_result.get('prs') and len(prs_result['prs']) > 0:
                # They have at least one assigned PR, skip the checklist
                st.session_state['page'] += 1
                st.rerun()
                return

    page_header(
        "Before You Start Reviewing",
        "Complete this quick checklist before beginning your assigned PR review."
    )
    assigned_repo = responses.get('assigned_repository')
    repo_url = responses.get('repository_url')
    pr_url = responses.get('pr_url')
    if not pr_url:
        assigned_pr = responses.get('assigned_pr') or {}
        pr_url = assigned_pr.get('url')
    if pr_url:
        try:
            repo_url = extract_repo_url(pr_url)
        except ValueError:
            repo_url = None
    if not assigned_repo and repo_url:
        path_parts = repo_url.strip('/').split('/')
        if len(path_parts) >= 2:
            assigned_repo = '/'.join(path_parts[-2:])

    if participant_id and (not assigned_repo or not responses.get('repository_url')):
        repo_result = get_repository_assignment(participant_id)
        if repo_result.get('success'):
            assigned_repo = repo_result['repository']
            responses['assigned_repository'] = assigned_repo
            if repo_result.get('url'):
                responses['repository_url'] = repo_result['url']

    repo_name = assigned_repo.split('/')[-1] if assigned_repo else None
    if not repo_name and repo_url:
        repo_name = repo_url.strip('/').split('/')[-1]
    fork_url = f"https://github.com/swe-productivity/{repo_name}" if repo_name else None

    previous = st.session_state['survey_responses'].get('setup_checklist', {})
    invitation_checked = st.checkbox(
        f"**{CHECKLIST_KEYS['invitation_accepted']}**",
        value=previous.get('invitation_accepted', False)
    )
    info_lines = []
    if repo_url:
        info_lines.append(f"Repository URL: {repo_url}")
    st.info("\n\n".join(info_lines))

    recorder_checked = st.checkbox(
        f"**{CHECKLIST_KEYS['recorder_ready']}**",
        value=previous.get('recorder_ready', False)
    )
    st.markdown(
        "Launch the recorder once to confirm it captures your review sessions correctly. You should see a `/data` directory with `screenshots/` and `actions.db`."
        " You can find the tool at [swe-prod-recorder](https://github.com/jennjwang/swe-prod-recorder)."
    )

    def persist_state():
        st.session_state['survey_responses']['setup_checklist'] = {
            'invitation_accepted': invitation_checked,
            'recorder_ready': recorder_checked
        }
        st.session_state['survey_responses']['setup_checklist_complete'] = invitation_checked and recorder_checked

    def validate():
        return invitation_checked and recorder_checked

    def handle_back():
        persist_state()
        save_and_navigate('back')

    def handle_next():
        if not validate():
            return
        persist_state()
        save_and_navigate('next')

    navigation_buttons(
        on_back=handle_back,
        on_next=handle_next,
        back_key="setup_checklist_back",
        next_key="setup_checklist_next",
        validation_fn=validate,
        validation_error="Please complete both checklist items before continuing."
    )
