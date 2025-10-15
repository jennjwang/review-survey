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


def pr_assignment_page():
    """Display the PR assignment page."""
    page_header(
        "PR Assignment",
        "Review the assigned PR for this study."
    )
    
    # Get participant info
    participant_id = st.session_state['survey_responses'].get('participant_id', '')
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository', 'N/A')
    repository_url = st.session_state['survey_responses'].get('repository_url', 'N/A')

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
    current_pr = st.session_state['survey_responses'].get('assigned_pr', None)
    if not current_pr and participant_id and assigned_repo and assigned_repo != 'N/A':
        fetched = get_assigned_pr_for_reviewer(participant_id, assigned_repo)
        if fetched['success'] and fetched['pr'] is not None:
            pr_data = fetched['pr']
            st.session_state['survey_responses']['assigned_pr'] = pr_data
            st.session_state['survey_responses']['pr_number'] = pr_data['number']
            st.session_state['survey_responses']['pr_title'] = pr_data['title']
            st.session_state['survey_responses']['pr_url'] = pr_data['url']
            st.session_state['survey_responses']['issue_id'] = pr_data['issue_id']
            st.session_state['survey_responses']['issue_url'] = pr_data['issue_url']
            current_pr = pr_data
    
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
                    st.session_state['survey_responses']['pr_number'] = pr_data['number']
                    st.session_state['survey_responses']['pr_title'] = pr_data['title']
                    st.session_state['survey_responses']['pr_url'] = pr_data['url']
                    st.session_state['survey_responses']['issue_id'] = pr_data['issue_id']
                    st.session_state['survey_responses']['issue_url'] = pr_data['issue_url']
                    
                    current_pr = pr_data
                    st.success(f"✅ Successfully assigned PR #{pr_data['number']}")
                    st.rerun()
                else:
                    st.error(f"⚠️ Error assigning PR: {assign_result['error']}")
            else:
                st.error(f"⚠️ {pr_result['error']}")
    
    # Display PR assignment
    if current_pr:
        st.info(f"""
        **Assigned PR for Review:**
        
        **Issue URL:** {current_pr.get('issue_url', 'N/A')}  
        **PR URL:** {current_pr.get('url', 'N/A')}
        """)
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    elif not participant_id or not assigned_repo or assigned_repo == 'N/A':
        st.warning("⚠️ Please complete the previous steps to get a PR assignment.")
    else:
        st.info("Assigning a PR to you...")
        st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # Pre-PR time estimate (only when PR assigned)
    reviewer_estimate = 'Not selected'
    if current_pr:
        ESTIMATE_OPTIONS = [
            "Not selected",
            "<30 minutes",
            "30–60 minutes",
            "1–2 hours",
            ">2 hours"
        ]

        previous_estimate = st.session_state['survey_responses'].get('reviewer_estimate', 'Not selected')
        reviewer_estimate = selectbox_question(
            "Before reviewing this PR, how long do you think it will take you to complete it?",
            ESTIMATE_OPTIONS,
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
            1. Review the assigned PR thoroughly<br>
            2. Complete the post-PR review survey<br>
            3. Engage in discussion with the contributor<br>
            4. Close or merge the PR as appropriate<br>
            5. Complete the post-PR closed survey
            </p>
            """, unsafe_allow_html=True)
    
    # Validation function - require estimate when PR is assigned
    def validate():
        if current_pr:
            return reviewer_estimate != "Not selected"
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
        # Save estimate to session and contributor DB
        if current_pr and reviewer_estimate != 'Not selected':
            st.session_state['survey_responses']['reviewer_estimate'] = reviewer_estimate
            issue_id = st.session_state['survey_responses'].get('issue_id')
            if issue_id:
                with st.spinner('Saving your estimate...'):
                    result = save_reviewer_estimate_for_issue(issue_id, reviewer_estimate)
                if not result.get('success'):
                    st.error(f"⚠️ Error saving estimate: {result.get('error')}")
                    return
            
            # Save session state
            participant_id = st.session_state['survey_responses'].get('participant_id')
            if participant_id:
                from survey_data import save_session_state
                save_session_state(participant_id, st.session_state.get('page', 0), st.session_state['survey_responses'])
            
            save_and_navigate('next', reviewer_estimate=reviewer_estimate)
        else:
            st.error("Please select an estimate before proceeding.")
    
    # Navigation
    navigation_buttons(
        on_back=handle_back,
        on_next=handle_next,
        back_key="pr_assignment_back",
        next_key="pr_assignment_next"
    )
