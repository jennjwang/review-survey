"""
Review submission confirmation page.
Asks the reviewer to confirm they have submitted their first PR review,
then routes to the post-PR-review question pages.
"""

import streamlit as st
from survey_components import page_header, selectbox_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context
from survey_data import get_repository_assignment, get_assigned_pr_for_reviewer, save_session_state, update_is_reviewed_for_issue
from drive_upload import upload_to_drive_in_subfolders, sanitize_filename


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

    st.markdown(
        "<p style='font-size:16px; margin-top: 1rem; margin-bottom: 1rem;'>"
        "<b>Important:</b> Remember to keep swe-prod-recorder running while you review the PR.</p>",
        unsafe_allow_html=True
    )

    st.markdown("<hr style='margin: 2rem 0;'>", unsafe_allow_html=True)

    # Main question section
    st.markdown("### Have you completed your initial review?")
    # st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    st.markdown("Please confirm that you have reviewed the PR thoroughly and provided feedback.")

    # st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # Store completion choice in session state to show/hide upload section
    if 'review_completion_choice' not in st.session_state:
        st.session_state['review_completion_choice'] = None

    # Create two-column layout for buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Yes, I've completed my review", key="review_yes", use_container_width=True, type="primary"):
            st.session_state['review_completion_choice'] = 'completed'

    with col2:
        if st.button("Not yet, still working on it", key="review_no", use_container_width=True):
            st.session_state['review_completion_choice'] = 'not_completed'

    # If user selected "completed", show file upload section
    if st.session_state.get('review_completion_choice') == 'completed':
        st.divider()
        st.subheader("Upload Screen Recorder Data")
        st.write("Please review your data to exclude any sensitive information before submitting.")

        st.caption("Upload a zipped copy of the `/data` folder from your swe-prod-recorder directory.")
        screenrec_upload = st.file_uploader(
            "Upload screen recorder /data folder (zipped)",
            type=['zip'],
            key="screenrec_upload",
            label_visibility="collapsed"
        )
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

        submit_button = st.button(
            "Submit and Continue",
            key="submit_review_completion",
            type="primary"
        )

        if submit_button:
            # Enforce upload present
            if not screenrec_upload:
                st.error("Please upload the screen recorder data zip before submitting.")
                return

            # Upload files to Drive
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
                    issue_folder = sanitize_filename(f"pr_{issue_id}") if issue_id else "unknown_pr"
                    review_status = "initial_review"
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

            # Save response
            st.session_state['survey_responses']['is_reviewed'] = "Yes - I've submitted my review"
            st.session_state['survey_responses']['artifacts_uploaded'] = True

            # Update is_reviewed flag in database
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
            if participant_id:
                save_session_state(participant_id, next_index, st.session_state['survey_responses'])
            st.session_state['page'] = next_index
            st.session_state['review_completion_choice'] = None  # Reset for next time
            st.rerun()

    # If user selected "not completed", show helpful message
    if st.session_state.get('review_completion_choice') == 'not_completed':
        st.divider()
        st.info("""
            No problem! Please continue working on your review.

            When you complete it and submit your review, return to this page to confirm completion.
        """)
        st.session_state['survey_responses']['is_reviewed'] = "Not yet"
