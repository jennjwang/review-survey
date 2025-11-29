"""
PR assignment page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, navigation_buttons, selectbox_question
from survey_utils import save_and_navigate
from survey_data import (
    get_random_unassigned_pr,
    assign_pr_to_reviewer,
    save_reviewer_estimate_for_issue,
    get_repository_assignment,
    get_assigned_pr_for_reviewer,
)


def _sync_artifact_status(issue_id, status=None):
    responses = st.session_state['survey_responses']
    artifact_map = responses.setdefault('artifact_upload_status', {})
    if issue_id is None:
        responses['artifact_upload_complete'] = False
        return
    key = str(issue_id)
    if status is None:
        status = artifact_map.get(key, False)
    artifact_map[key] = status
    responses['artifact_upload_complete'] = status


def pr_assignment_page():
    """Display the PR assignment page."""
    # Get participant info
    participant_id = st.session_state['survey_responses'].get('participant_id', '')
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository', 'N/A')
    repository_url = st.session_state['survey_responses'].get('repository_url', 'N/A')

    # Check if PR is already assigned with time estimates - if so, skip this page
    current_pr = st.session_state['survey_responses'].get('assigned_pr', None)
    if current_pr:
        reviewer_estimate = current_pr.get('reviewer_estimate') or st.session_state['survey_responses'].get('reviewer_estimate')
        new_contributor_estimate = current_pr.get('new_contributor_estimate') or st.session_state['survey_responses'].get('new_contributor_estimate')

        # If both estimates are provided and not "Not selected", skip this page
        if (reviewer_estimate and reviewer_estimate != 'Not selected' and
            new_contributor_estimate and new_contributor_estimate != 'Not selected'):
            print("[DEBUG] Skipping PR assignment page: PR already assigned with time estimates")
            st.session_state['page'] += 1
            st.rerun()
            return

    # Check database for assigned PR if not in session state
    if not current_pr and participant_id and assigned_repo and assigned_repo != 'N/A':
        fetched = get_assigned_pr_for_reviewer(participant_id, assigned_repo)
        if fetched['success'] and fetched['pr'] is not None:
            pr_data = fetched['pr']
            reviewer_estimate_db = pr_data.get('reviewer_estimate')
            new_contributor_estimate_db = pr_data.get('new_contributor_estimate')

            # If both estimates are provided in DB, skip this page
            if (reviewer_estimate_db and reviewer_estimate_db != 'Not selected' and
                new_contributor_estimate_db and new_contributor_estimate_db != 'Not selected'):
                print("[DEBUG] Skipping PR assignment page: Found PR in DB with time estimates")
                # Store in session state before skipping
                st.session_state['survey_responses']['assigned_pr'] = pr_data
                st.session_state['survey_responses']['pr_url'] = pr_data['url']
                st.session_state['survey_responses']['issue_id'] = pr_data['issue_id']
                st.session_state['survey_responses']['issue_url'] = pr_data['issue_url']
                st.session_state['survey_responses']['reviewer_estimate'] = reviewer_estimate_db
                st.session_state['survey_responses']['new_contributor_estimate'] = new_contributor_estimate_db
                st.session_state['page'] += 1
                st.rerun()
                return

    page_header(
        "PR Assignment",
        "Please provide time estimates for the following before reviewing the assigned PR."
    )

    # If repository assignment is missing (e.g., after resume), fetch it now
    if participant_id and (not assigned_repo or assigned_repo == 'N/A'):
        try:
            repo_result = get_repository_assignment(participant_id)
            if repo_result['success']:
                assigned_repo = repo_result['repository']
                repository_url = repo_result['url']
                st.session_state['survey_responses']['assigned_repository'] = assigned_repo
                st.session_state['survey_responses']['repository_url'] = repository_url
            else:
                st.warning("⚠️ Could not load your repository assignment; please go back and re-enter your Participant ID.")
        except Exception:
            st.warning("⚠️ Could not load your repository assignment; please go back and re-enter your Participant ID.")

    # Check if PR is already in session or fetch from repo-issues by reviewer_id
    no_pr_available = False
    current_pr = st.session_state['survey_responses'].get('assigned_pr', None)
    estimates_already_provided = False

    if not current_pr and participant_id and assigned_repo and assigned_repo != 'N/A':
        fetched = get_assigned_pr_for_reviewer(participant_id, assigned_repo)
        if fetched['success'] and fetched['pr'] is not None:
            pr_data = fetched['pr']
            st.session_state['survey_responses']['assigned_pr'] = pr_data
            st.session_state['survey_responses']['pr_url'] = pr_data['url']
            st.session_state['survey_responses']['issue_id'] = pr_data['issue_id']
            st.session_state['survey_responses']['issue_url'] = pr_data['issue_url']
            current_pr = pr_data
            _sync_artifact_status(pr_data.get('issue_id'))

            # Check if estimates have already been provided
            reviewer_estimate_db = pr_data.get('reviewer_estimate')
            new_contributor_estimate_db = pr_data.get('new_contributor_estimate')
            if reviewer_estimate_db and new_contributor_estimate_db:
                estimates_already_provided = True
                st.session_state['survey_responses']['reviewer_estimate'] = reviewer_estimate_db
                st.session_state['survey_responses']['new_contributor_estimate'] = new_contributor_estimate_db
    
    # Automatically assign a PR if not already assigned
    if not current_pr and participant_id and assigned_repo != 'N/A':
        with st.spinner('Finding an available PR for you to review...'):
            # Get a random unassigned PR
            pr_result = get_random_unassigned_pr(assigned_repo)
            
            if pr_result['success']:
                pr_data = pr_result['pr']
                
                # Assign the PR to the reviewer
                assign_result = assign_pr_to_reviewer(participant_id, pr_data['issue_id'])
                
                if assign_result['success']:
                    # Store PR info in session state
                    st.session_state['survey_responses']['assigned_pr'] = pr_data
                    st.session_state['survey_responses']['pr_url'] = pr_data['url']
                    st.session_state['survey_responses']['issue_id'] = pr_data['issue_id']
                    st.session_state['survey_responses']['issue_url'] = pr_data['issue_url']
                    
                    _sync_artifact_status(pr_data.get('issue_id'), status=False)

                    current_pr = pr_data
                    st.success(f"✅ Successfully assigned PR #{pr_data['number']}")
                    st.rerun()
                else:
                    st.warning(f"⚠️ Error assigning PR: {assign_result['error']}")
                    no_pr_available = True
            else:
                st.warning(f"⚠️ {pr_result['error']}")
                no_pr_available = True
    
    # Check if estimates have already been provided (from session or database)
    if current_pr and not estimates_already_provided:
        reviewer_estimate_db = current_pr.get('reviewer_estimate')
        new_contributor_estimate_db = current_pr.get('new_contributor_estimate')
        if reviewer_estimate_db and new_contributor_estimate_db:
            estimates_already_provided = True
            st.session_state['survey_responses']['reviewer_estimate'] = reviewer_estimate_db
            st.session_state['survey_responses']['new_contributor_estimate'] = new_contributor_estimate_db

    # Display PR assignment
    if current_pr:
        st.info(f"""
        **Issue URL:** {current_pr.get('issue_url', 'N/A')}\n
        **PR URL:** {current_pr.get('url', 'N/A')}
        """)
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    elif not participant_id or not assigned_repo or assigned_repo == 'N/A':
        st.warning("⚠️ Please complete the previous steps to get a PR assignment.")
    else:
        st.info("Assigning a PR to you...")
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    # Pre-PR time estimate (when PR assigned or estimates still needed)
    reviewer_estimate = 'Not selected'
    new_contributor_estimate = 'Not selected'

    # Show estimate questions only if not already provided
    if (current_pr or no_pr_available) and not estimates_already_provided:
        NEW_CONTRIBUTOR_OPTIONS = [
            "Not selected",
            "<30 minutes",
            "30–60 minutes",
            "1–2 hours",
            "2–4 hours",
            ">4 hours"
        ]
        REVIEWER_OPTIONS = [
            "Not selected",
            "<30 minutes",
            "30–60 minutes",
            "1–2 hours",
            ">2 hours"
        ]

        previous_new_contributor_estimate = st.session_state['survey_responses'].get('new_contributor_estimate', 'Not selected')
        new_contributor_estimate = selectbox_question(
            "Before starting your review, how long do you think it took a <em>new contributor</em> to complete this PR?",
            NEW_CONTRIBUTOR_OPTIONS,
            "new_contributor_estimate",
            previous_new_contributor_estimate,
            placeholder="Select an estimate"
        )

        previous_estimate = st.session_state['survey_responses'].get('reviewer_estimate', 'Not selected')
        reviewer_estimate = selectbox_question(
            "Before starting your review, how long do you think it will take you to review this PR?",
            REVIEWER_OPTIONS,
            "reviewer_estimate",
            previous_estimate,
            placeholder="Select an estimate"
        )

        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

        # Next Steps
        st.markdown("""
            <p style='font-size:18px; margin-top: 1rem'>
            <strong>Next Steps:</strong>
            </p>
            <p style='font-size:18px'>
            1. Assign the PR to yourself<br>
            2. Review the assigned PR thoroughly - make sure to use the recording tool to capture your review session<br>
            3. Complete a short survey after your initial review of the PR<br>
            4. Engage in discussion with the contributor - make sure to use the recording tool to capture this session<br>
            5. Close or merge the PR as appropriate<br>
            6. Complete the final survey reflecting on your review experience
            </p>
            """, unsafe_allow_html=True)

    # Validation function - require estimates whenever prompts are shown, or allow if already provided
    def validate():
        if estimates_already_provided:
            return True
        if (current_pr or no_pr_available) and not estimates_already_provided:
            return (
                reviewer_estimate != "Not selected" and
                new_contributor_estimate != "Not selected"
            )
        return False
    
    # Custom navigation handlers
    def handle_back():
        # Save session state before going back
        participant_id = st.session_state['survey_responses'].get('participant_id')
        if participant_id:
            from survey_data import save_session_state
            save_session_state(participant_id, st.session_state.get('page', 0), st.session_state['survey_responses'])
        save_and_navigate('back')
    
    def handle_next():
        if not validate():
            st.error("Please select an estimate before proceeding.")
            return

        # If estimates already provided, just navigate
        if estimates_already_provided:
            saved_reviewer_estimate = st.session_state['survey_responses'].get('reviewer_estimate')
            saved_new_contributor_estimate = st.session_state['survey_responses'].get('new_contributor_estimate')

            # Save session state
            participant_id = st.session_state['survey_responses'].get('participant_id')
            if participant_id:
                from survey_data import save_session_state
                save_session_state(participant_id, st.session_state.get('page', 0), st.session_state['survey_responses'])

            save_and_navigate(
                'next',
                reviewer_estimate=saved_reviewer_estimate,
                new_contributor_estimate=saved_new_contributor_estimate
            )
        # Otherwise, save new estimates to session and contributor DB
        elif (current_pr or no_pr_available):
            st.session_state['survey_responses']['reviewer_estimate'] = reviewer_estimate
            st.session_state['survey_responses']['new_contributor_estimate'] = new_contributor_estimate
            issue_id = st.session_state['survey_responses'].get('issue_id')
            if issue_id:
                with st.spinner('Saving your estimate...'):
                    result = save_reviewer_estimate_for_issue(
                        issue_id,
                        reviewer_estimate,
                        new_contributor_estimate=new_contributor_estimate
                    )
                if not result.get('success'):
                    st.error(f"⚠️ Error saving estimate: {result.get('error')}")
                    return

            # Save session state
            participant_id = st.session_state['survey_responses'].get('participant_id')
            if participant_id:
                from survey_data import save_session_state
                save_session_state(participant_id, st.session_state.get('page', 0), st.session_state['survey_responses'])

            save_and_navigate(
                'next',
                reviewer_estimate=reviewer_estimate,
                new_contributor_estimate=new_contributor_estimate
            )
    
    # Navigation
    navigation_buttons(
        on_back=handle_back,
        on_next=handle_next,
        back_key="pr_assignment_back",
        next_key="pr_assignment_next"
    )
