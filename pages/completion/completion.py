"""
Survey completion page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, navigation_buttons
from survey_utils import next_page
from survey_data import save_session_state


def completion_page():
    """Display the survey completion page."""
    page_header(
        "Survey Complete",
    )
    
    st.markdown("""
        <p style='font-size:20px'>
        Your responses have been recorded and will be used for research purposes.
        </p>
        
        <p style='font-size:20px'>
        Thank you for your contribution to this research!
        </p>
        """, unsafe_allow_html=True)
    
    # Display summary of responses
    with st.expander("View your responses"):
        st.json(st.session_state['survey_responses'])
    
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
        <p style='font-size:18px; text-align: center; margin-top: 2rem; color: #666;'>
        You may now close this window.
        </p>
        """, unsafe_allow_html=True)
