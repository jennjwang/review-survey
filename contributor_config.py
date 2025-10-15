"""
Configuration for connecting to the contributor's Supabase database.
This allows the reviewer survey to access contributor data (repo-issues table).
"""

import os


def get_contributor_db_creds():
    """Fetch contributor DB URL/KEY from Streamlit secrets or environment variables."""
    url = None
    key = None
    try:
        import streamlit as st
        url = st.secrets.get('CONTRIBUTOR_SUPABASE_URL')
        key = st.secrets.get('CONTRIBUTOR_SUPABASE_KEY')
    except Exception:
        # Streamlit might not be available during certain import contexts
        pass

    if not url:
        url = os.getenv('CONTRIBUTOR_SUPABASE_URL')
    if not key:
        key = os.getenv('CONTRIBUTOR_SUPABASE_KEY')

    return url, key


# Table names in the contributor database
CONTRIBUTOR_TABLES = {
    'participant_repos': 'participant-repos',
    'repo_issues': 'repo-issues'
}
