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
    assign_pr_to_reviewer,
    get_participant_progress,
    get_prs_with_incomplete_responses,
    MIN_COMPLETED_REVIEWS
)
from drive_upload import upload_to_drive_in_subfolders, sanitize_filename


STATUS_OPTIONS = [
    "Still open - review in progress",
    "Merged - PR was accepted and merged",
    "Closed without merging - PR was rejected or abandoned"
]


def pr_status_page():
    """Display the PR status page."""
    st.header("PR Review Status")
    st.markdown("""
        <p style='font-size:18px; font-weight: 400; margin-bottom: 2rem'>
        Thank you for reviewing the PR! <br><br>
        Please update the status of your assigned PR below once it has been merged or closed. 
        If you would like to review another PR, you can request one below. <br><br>
        <b>Important:</b> Remember to keep swe-prod-recorder running while you review and discuss the PR.
        """, unsafe_allow_html=True)

    participant_id = st.session_state['survey_responses'].get('participant_id')
    completed_count = None
    remaining = None
    if participant_id:
        progress_result = get_participant_progress(participant_id)
        if progress_result.get('success') and progress_result.get('progress'):
            completed_count = progress_result['progress'].get('post_pr_review_count', 0)
            remaining = max(MIN_COMPLETED_REVIEWS - completed_count, 0)
    if completed_count is not None and remaining is not None:
        if remaining > 0:
            st.info(
                f"You have reviewed {completed_count} PR(s) so far. Review {remaining} more to finish the study."
            )
        else:
            st.success(
                f"You've reviewed {completed_count} PR(s) — you've met the study minimum."
            )

    # Load all PRs assigned to this reviewer; allow status update for any
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository')
    if participant_id and not assigned_repo:
        repo_result = get_repository_assignment(participant_id)
        if repo_result['success']:
            assigned_repo = repo_result['repository']
            st.session_state['survey_responses']['assigned_repository'] = assigned_repo
            st.session_state['survey_responses']['repository_url'] = repo_result['url']

    # Check for PRs with incomplete post-PR-review responses
    incomplete_prs = []
    if participant_id and assigned_repo:
        incomplete_result = get_prs_with_incomplete_responses(participant_id, assigned_repo)
        if incomplete_result['success']:
            incomplete_prs = incomplete_result.get('incomplete_prs', [])
    
    # If there are incomplete responses, show warning and redirect option
    if incomplete_prs:
        st.warning(f"⚠️ You have {len(incomplete_prs)} PR(s) with incomplete survey responses. Please complete them before requesting a new PR.")
        
        for incomplete_pr in incomplete_prs:
            pr_url_incomplete = incomplete_pr.get('pr_url', 'Unknown PR')
            missing = incomplete_pr.get('missing_fields', [])
            
            col1, col2 = st.columns([3, 1], vertical_alignment="center")
            with col1:
                st.markdown("<p style='margin-top: 0.4rem;'></p>", unsafe_allow_html=True)
                st.markdown(f"**{pr_url_incomplete}**")
            with col2:
                if st.button("Complete Survey", key=f"complete_{incomplete_pr.get('issue_id')}", use_container_width=True):
                    # Set up session state for this PR and redirect to the appropriate page
                    st.session_state['survey_responses']['pr_url'] = incomplete_pr.get('pr_url')
                    st.session_state['survey_responses']['issue_url'] = incomplete_pr.get('issue_url')
                    st.session_state['survey_responses']['issue_id'] = incomplete_pr.get('issue_id')
                    
                    # Clear widget state to ensure fresh input
                    widget_keys_to_clear = [
                        'ai_review_strategy_text', 'ai_reasoning_text', 'ai_likelihood',
                        'nasa_tlx_mental_demand', 'nasa_tlx_physical_demand', 'nasa_tlx_frustration',
                        'code_quality_readability', 'code_quality_analyzability',
                        'code_quality_modifiability', 'code_quality_testability',
                        'code_quality_stability', 'code_quality_correctness',
                        'code_quality_compliance',
                    ]
                    for widget_key in widget_keys_to_clear:
                        if widget_key in st.session_state:
                            del st.session_state[widget_key]
                    
                    # Clear session state responses to force fresh input
                    st.session_state['survey_responses']['nasa_tlx_responses'] = {}
                    st.session_state['survey_responses']['code_quality_responses'] = {}
                    st.session_state['survey_responses']['ai_likelihood'] = None
                    st.session_state['survey_responses']['ai_reasoning'] = ''
                    st.session_state['survey_responses']['ai_review_strategy'] = ''
                    
                    # Determine which page to go to based on missing fields
                    if 'nasa_tlx' in missing:
                        st.session_state['page'] = 5  # nasa_tlx_questions_page
                    elif 'code_quality' in missing:
                        st.session_state['page'] = 6  # code_quality_ratings_page
                    elif 'ai_detection' in missing:
                        st.session_state['page'] = 7  # ai_detection_page
                    else:
                        st.session_state['page'] = 5  # Default to NASA TLX
                    
                    st.rerun()
        
        st.divider()

    pr_url = st.session_state['survey_responses'].get('pr_url')
    
    pr_choices = []
    if participant_id and assigned_repo:
        assigned = list_assigned_prs_for_reviewer(participant_id, assigned_repo)
        if assigned['success'] and assigned['prs']:
            pr_choices = [
                pr for pr in assigned['prs']
                if not pr.get('is_closed') and not pr.get('is_merged')
            ]

    def request_another_pr(button_key: str):
        if participant_id and assigned_repo:
            # Disable button if there are incomplete responses
            button_disabled = len(incomplete_prs) > 0
            if st.button("Request another PR", key=button_key, use_container_width=True, disabled=button_disabled):
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
                            st.session_state['survey_responses']['new_contributor_estimate'] = 'Not selected'
                            st.session_state['survey_responses']['pr_status'] = 'Still open - review in progress'
                            artifact_map = st.session_state['survey_responses'].setdefault('artifact_upload_status', {})
                            if pr_data.get('issue_id') is not None:
                                artifact_map[str(pr_data['issue_id'])] = False
                            st.session_state['survey_responses']['artifact_upload_complete'] = False
                            
                            # Clear post-PR-review responses from previous PR to prevent carryover
                            # BUG FIX: Streamlit caches widget values by their `key` parameter.
                            # The `value` param only sets the initial value on first render;
                            # afterwards, the cached widget state takes precedence. This caused
                            # responses from the first PR to appear pre-filled for all subsequent PRs.
                            # 
                            # Affected fields in reviewer-post-pr-review table:
                            #   - nasa_tlx_* (all NASA TLX questions)
                            #   - code_quality_* (all code quality questions)
                            #   - ai_likelihood, ai_reasoning, ai_review_strategy
                            st.session_state['survey_responses']['nasa_tlx_responses'] = {}
                            st.session_state['survey_responses']['code_quality_responses'] = {}
                            st.session_state['survey_responses']['ai_likelihood'] = None
                            st.session_state['survey_responses']['ai_reasoning'] = ''
                            st.session_state['survey_responses']['ai_review_strategy'] = ''
                            st.session_state['survey_responses']['is_reviewed'] = None
                            st.session_state['survey_responses']['artifacts_uploaded'] = False
                            
                            # CRITICAL: Clear all Streamlit widget keys for post-PR-review questions.
                            # Without this, widgets ignore the `value` param and show cached values.
                            widget_keys_to_clear = [
                                # AI detection text areas
                                'ai_review_strategy_text', 'ai_reasoning_text',
                                # AI likelihood slider
                                'ai_likelihood',
                                # NASA TLX sliders
                                'nasa_tlx_mental_demand', 'nasa_tlx_physical_demand', 'nasa_tlx_frustration',
                                # Code quality sliders
                                'code_quality_readability', 'code_quality_analyzability',
                                'code_quality_modifiability', 'code_quality_testability',
                                'code_quality_stability', 'code_quality_correctness',
                                'code_quality_compliance',
                            ]
                            for widget_key in widget_keys_to_clear:
                                if widget_key in st.session_state:
                                    del st.session_state[widget_key]
                            
                            # Send the reviewer back to the estimate + assignment step for the new PR
                            st.session_state['page'] = 3  # pr_assignment_page
                            st.rerun()
                        else:
                            return f"Error assigning PR: {assign_result['error']}"
                    else:
                        return f"{pr_result.get('error') or 'No unassigned PRs available in this repo.'}"
        return None

    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    if not pr_choices:
        st.info("All of your reviewed PRs have been merged or closed. Please request another PR.")
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        assignment_error = request_another_pr("assign_another_pr_empty")
        if assignment_error:
            st.error(assignment_error)
        return
    else:
        assignment_error = request_another_pr("assign_another_pr_not_empty")
        if assignment_error:
            st.error(assignment_error)

    st.divider()

    labels = [f"PR #{p['number']}: {p['url']}" if p['number'] != 'N/A' else p['title'] for p in pr_choices]

    st.subheader("Update PR Status")
    st.markdown(
        "<p style='font-size:18px; font-weight: 400; margin-bottom:0.5rem;'>Select a PR:</p>",
        unsafe_allow_html=True
    )
    selected_label = st.selectbox("", labels, index=0, label_visibility="collapsed")

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    idx = labels.index(selected_label)
    pr = pr_choices[idx]
    pr_url = pr['url']
    st.session_state['survey_responses']['pr_url'] = pr_url
    st.session_state['survey_responses']['issue_id'] = pr.get('issue_id')
    artifact_map = st.session_state['survey_responses'].setdefault('artifact_upload_status', {})
    if pr.get('issue_id') is not None:
        issue_key = str(pr['issue_id'])
    else:
        issue_key = pr_url or 'current_pr'
    st.session_state['survey_responses']['artifact_upload_complete'] = artifact_map.get(issue_key, False)

    if pr_url:
        st.info(f"**Link to PR:** [{pr_url}]({pr_url})")
    else:
        st.warning("⚠️ No PR assigned yet.")

    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

    # Set default PR status if not already set
    if 'pr_status' not in st.session_state['survey_responses']:
        st.session_state['survey_responses']['pr_status'] = 'Still open - review in progress'

    previous_value = st.session_state['survey_responses']['pr_status']

    pr_status = selectbox_question(
        "What is the current status of this PR?",
        STATUS_OPTIONS,
        "pr_status",
        previous_value
    )

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Show info box if PR is still in progress
    if pr_status == "Still open - review in progress":
        st.info("""
        - Please continue collaborating with the contributor until the PR is ready to merge.
        - If there's no response for 2+ weeks, you may close the PR as abandoned.
        - Return here to update the status once the PR is merged or closed.""")
        st.markdown("<div style='margin-top: 5rem;'></div>", unsafe_allow_html=True)

    # Show upload section if PR is merged or closed
    if pr_status in ["Merged - PR was accepted and merged", "Closed without merging - PR was rejected or abandoned"]:
        st.divider()
        st.subheader("Upload Screen Recorder Data")
        st.write("Please review your data to exclude any sensitive information before submitting.")
        st.info("**Large files (>1GB):** If your recording is too large, please use **[this Google Form](https://forms.gle/Yk5TcwhEveMNCF1g8)** instead.")

        st.caption("Upload a zipped copy of the `/data` folder from your swe-prod-recorder directory for this PR review.")
        screenrec_upload = st.file_uploader(
            "Upload screen recorder /data folder (zipped)",
            type=['zip'],
            key="screenrec_upload_closed",
            label_visibility="collapsed"
        )

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        submit_button = st.button(
            "Submit and Continue",
            key="submit_pr_closed",
            type="primary"
        )
        

        if submit_button:
            # Enforce upload present
            if not screenrec_upload:
                st.error("Please upload the screen recorder data zip before submitting.")
                return
            
            # Check file size (1GB limit)
            MAX_FILE_SIZE_GB = 1
            MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_GB * 1024 * 1024 * 1024
            if screenrec_upload.size > MAX_FILE_SIZE_BYTES:
                st.error(f"File size exceeds {MAX_FILE_SIZE_GB}GB limit. Please reduce the file size and try again.")
                return

            # Upload file to Drive
            try:
                folder_id = (
                    st.secrets.get('REVIEWER_GDRIVE_FOLDER_ID') or
                    st.secrets.get('GDRIVE_FOLDER_ID')
                )
                if not folder_id:
                    st.error("Drive folder not configured. Ask the study team to set REVIEWER_GDRIVE_FOLDER_ID in secrets.")
                    return

                with st.spinner('Uploading your file...'):
                    participant_folder = sanitize_filename(participant_id) if participant_id else "unknown_participant"
                    current_issue_id = st.session_state['survey_responses'].get('issue_id')
                    issue_folder = sanitize_filename(f"pr_{current_issue_id}") if current_issue_id else "unknown_pr"
                    review_status = "final_review"
                    subfolders = [participant_folder, issue_folder, review_status]

                    # Upload screen recorder zip
                    upload_to_drive_in_subfolders(
                        screenrec_upload,
                        folder_id,
                        subfolders=subfolders,
                        filename=screenrec_upload.name,
                    )
                st.success("Upload completed successfully!")
            except Exception as e:
                st.error(f"Upload failed: {e}")
                return

            # Update PR status in database
            st.session_state['survey_responses']['pr_status'] = pr_status
            issue_id = st.session_state['survey_responses'].get('issue_id')
            if issue_id:
                is_merged = pr_status == "Merged - PR was accepted and merged"
                is_closed = pr_status == "Closed without merging - PR was rejected or abandoned"
                result = update_contributor_repo_issues_status(issue_id, is_closed, is_merged, True)
                if not result['success']:
                    st.warning(f"Error updating PR status: {result['error']}")

            # Navigate to next page
            save_and_navigate('next', pr_status=pr_status)
