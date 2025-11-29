"""
Data layer for reviewer survey database operations.
"""

from postgrest import APIError
from supabase import create_client
from contributor_config import get_contributor_db_creds, CONTRIBUTOR_TABLES
from survey_questions import NASA_TLX_QUESTIONS, CODE_QUALITY_QUESTIONS

MIN_COMPLETED_REVIEWS = 4


# Initialize Supabase client for reviewer data
def get_supabase_client():
    """Get initialized Supabase client for reviewer data based on mode."""
    import streamlit as st
    if st.secrets['MODE'] == 'dev':
        return create_client(
            st.secrets['SUPABASE_DEV_URL'],
            st.secrets['SUPABASE_DEV_KEY'],
        )
    elif st.secrets['MODE'] == 'prod':
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"],
        )
    return None


# Initialize Supabase client for contributor data (repo-issues table)
def get_contributor_supabase_client():
    """Get initialized Supabase client for contributor data (repo-issues table)."""
    try:
        url, key = get_contributor_db_creds()
        if not url or not key:
            print("Contributor database credentials not found in secrets")
            return None
        return create_client(url, key)
    except Exception as e:
        print(f"Error creating contributor client: {e}")
        return None


supabase_client = get_supabase_client()
# Don't initialize contributor_client at module level - initialize when needed


def _is_missing_table_error(error):
    """Return True if the PostgREST error indicates a missing table."""
    if not isinstance(error, APIError):
        return False
    payload = error.args[0] if error.args else {}
    if isinstance(payload, dict):
        return payload.get('code') == 'PGRST205'
    return False


def _safe_participant_query(table_name: str, participant_id: str):
    """Select rows for a participant, treating missing tables as empty results."""
    if not supabase_client:
        return []
    try:
        response = supabase_client.table(table_name).select('*').eq('participant_id', participant_id).execute()
        return response.data or []
    except APIError as api_err:
        if _is_missing_table_error(api_err):
            print(
                f"[WARN] Table '{table_name}' not found when querying participant '{participant_id}'. Returning empty list."
            )
            return []
        raise


def get_repository_assignment(participant_id: str):
    """
    Get repository assignment for a reviewer participant.
    
    Args:
        participant_id: The participant's ID
        
    Returns:
        dict with 'success', 'repository' (formatted as repository), 'url', and 'error' keys
    """
    if not supabase_client:
        return {
            'success': False,
            'error': 'Database client not initialized',
            'repository': None,
            'url': None
        }
    
    try:
        # Query the reviewer database for repository assignment
        response = supabase_client.table('reviewer-repos').select('*').eq('participant_id', participant_id).execute()
        print(f"Query for participant_id='{participant_id}'")
        print(f"Response: {response}")
        
        if response.data and len(response.data) > 0:
            # Get repository info from response
            row = response.data[0]
            print(f"Row data: {row}")
            
            # Extract repository details
            # owner = row.get('repository_owner')
            repository_name = row.get('repository_name')
            repository_url = row.get('repository_url')
            
            # print(f"Owner: {owner}")
            print(f"Repository name: {repository_name}")
            print(f"Repository URL: {repository_url}")
            
            if repository_name:
                return {
                    'success': True,
                    'repository': f"{repository_name}",
                    'url': repository_url,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': f"Repository information incomplete. Available columns: {list(row.keys())}",
                    'repository': None,
                    'url': None
                }
        else:
            # Try to get all records to debug
            all_records = supabase_client.table('reviewer-repos').select('participant_id').limit(5).execute()
            print(f"Sample participant IDs in table: {[r.get('participant_id') for r in all_records.data if all_records.data]}")
            return {
                'success': False,
                'error': f"Participant ID '{participant_id}' not found in the system. Please check your ID and try again.",
                'repository': None,
                'url': None
            }
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error retrieving repository assignment: {str(e)}",
            'repository': None,
            'url': None
        }

def update_contributor_repo_issues_status(issue_id: int, is_closed: bool, is_merged: bool, is_reviewed: bool):
    """
    Update PR status fields in the contributor project's repo-issues table.
    """
    contributor_client = get_contributor_supabase_client()
    if not contributor_client:
        return {'success': False, 'error': 'Contributor database client not initialized'}
    try:
        update_fields = {
            "is_closed": is_closed,
            "is_merged": is_merged,
            "is_reviewed": is_reviewed
        }
        response = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']).update(update_fields).eq('issue_id', issue_id).execute()
        if response.data and len(response.data) > 0:
            return {'success': True, 'error': None}
        else:
            return {'success': False, 'error': 'No matching issue to update.'}
    except Exception as e:
        return {'success': False, 'error': f"Error updating repo-issues: {e}"}


def update_is_reviewed_for_issue(issue_id: int, is_reviewed: bool = True):
    contributor_client = get_contributor_supabase_client()
    if not contributor_client:
        return {'success': False, 'error': 'Contributor database client not initialized'}
    try:
        resp = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']) \
            .update({'is_reviewed': is_reviewed}) \
            .eq('issue_id', issue_id) \
            .execute()
        if resp.data and len(resp.data) > 0:
            return {'success': True, 'error': None}
        else:
            return {'success': False, 'error': "Update failed (RLS or not found)"}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def validate_participant_id(participant_id: str):
    """
    Validate that a participant ID exists in the database.
    
    Args:
        participant_id: The participant's ID to validate
        
    Returns:
        dict with 'valid' (bool), 'error' (str or None) keys
    """
    if not supabase_client:
        return {
            'valid': False,
            'error': 'Database client not initialized'
        }
    
    if not participant_id or not participant_id.strip():
        return {
            'valid': False,
            'error': 'Participant ID cannot be empty'
        }
    
    try:
        # Check if participant ID exists in reviewer's participant-repos table
        response = supabase_client.table('reviewer-repos').select('participant_id').eq('participant_id', participant_id).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Participant ID '{participant_id}' validated successfully")
            return {
                'valid': True,
                'error': None
            }
        else:
            print(f"Participant ID '{participant_id}' not found in database")
            return {
                'valid': False,
                'error': f"Participant ID '{participant_id}' not found in the system. Please check your ID and try again."
            }
            
    except Exception as e:
        print(f"Error validating participant ID: {e}")
        import traceback
        traceback.print_exc()
        
        # Check if it's a type conversion error (invalid format for bigint)
        error_str = str(e)
        if 'invalid input syntax for type bigint' in error_str or '22P02' in error_str:
            return {
                'valid': False,
                'error': f"Participant ID '{participant_id}' not found in the system. Please check your ID and try again."
            }
        
        return {
            'valid': False,
            'error': f"Participant ID '{participant_id}' not found in the system. Please check your ID and try again."
        }


def save_post_pr_review_responses(participant_id: str, pr_url: str, responses: dict):
    """
    Save post-PR review responses to Supabase reviewer-post-pr-review table.
    
    Args:
        participant_id: The participant's ID
        pr_url: The PR URL
        responses: Dictionary of all survey responses
        
    Returns:
        dict with 'success' and 'error' keys
    """
    if not supabase_client:
        return {
            'success': False,
            'error': 'Database client not initialized'
        }
    
    try:
        from datetime import datetime, timezone
        
        # Prepare data for insertion
        data = {
            'participant_id': participant_id,
            'pr_url': pr_url,
        }
        
        # Add NASA-TLX responses
        nasa_tlx_responses = responses.get('nasa_tlx_responses', {})
        for key, value in nasa_tlx_responses.items():
            data[f'nasa_tlx_{key}'] = value
        
        # Add code quality responses
        code_quality_responses = responses.get('code_quality_responses', {})
        for key, value in code_quality_responses.items():
            data[f'code_quality_{key}'] = value
        
        # Add AI detection responses
        data['ai_likelihood'] = responses.get('ai_likelihood')
        data['ai_reasoning'] = responses.get('ai_reasoning')
        data['ai_review_strategy'] = responses.get('ai_review_strategy')
        
        print(f"Prepared post-PR review data for participant {participant_id}: {data}")
        
        # Check if participant already has responses for this PR
        existing = supabase_client.table('reviewer-post-pr-review').select('participant_id').eq('participant_id', participant_id).eq('pr_url', pr_url).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            data['updated_at'] = datetime.now(timezone.utc).isoformat()
            result = supabase_client.table('reviewer-post-pr-review').update(data).eq('participant_id', participant_id).eq('pr_url', pr_url).execute()
            print(f"Updated post-PR review responses for participant: {participant_id}, PR: {pr_url}")
        else:
            # Insert new record
            now = datetime.now(timezone.utc).isoformat()
            data['created_at'] = now
            data['updated_at'] = now
            result = supabase_client.table('reviewer-post-pr-review').insert(data).execute()
            print(f"Inserted post-PR review responses for participant: {participant_id}, PR: {pr_url}")
        
        return {
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"Error saving post-PR review responses: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error saving post-PR review responses: {str(e)}"
        }


def save_post_pr_closed_responses(participant_id: str, pr_url: str, responses: dict):
    """
    Save post-PR closed responses to Supabase reviewer-post-pr-closed table.
    
    Args:
        participant_id: The participant's ID
        pr_url: The PR URL
        responses: Dictionary of all survey responses
        
    Returns:
        dict with 'success' and 'error' keys
    """
    if not supabase_client:
        return {
            'success': False,
            'error': 'Database client not initialized'
        }
    
    try:
        from datetime import datetime, timezone
        
        # Prepare data for insertion
        data = {
            'participant_id': participant_id,
            'pr_url': pr_url,
        }
        
        # Add collaboration responses
        collaboration_responses = responses.get('collaboration_responses', {})
        for key, value in collaboration_responses.items():
            data[f'collaboration_{key}'] = value
        
        data['collaboration_description'] = responses.get('collaboration_description')
        
        # Add perception responses
        perception_responses = responses.get('perception_responses', {})
        for key, value in perception_responses.items():
            data[f'perception_{key}'] = value
        
        data['perception_description'] = responses.get('perception_description')
        data['perception_effort'] = responses.get('perception_effort')
        
        print(f"Prepared post-PR closed data for participant {participant_id}: {data}")
        
        # Check if participant already has responses for this PR
        existing = supabase_client.table('reviewer-post-pr-closed').select('participant_id').eq('participant_id', participant_id).eq('pr_url', pr_url).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            data['updated_at'] = datetime.now(timezone.utc).isoformat()
            result = supabase_client.table('reviewer-post-pr-closed').update(data).eq('participant_id', participant_id).eq('pr_url', pr_url).execute()
            print(f"Updated post-PR closed responses for participant: {participant_id}, PR: {pr_url}")
        else:
            # Insert new record
            now = datetime.now(timezone.utc).isoformat()
            data['created_at'] = now
            data['updated_at'] = now
            result = supabase_client.table('reviewer-post-pr-closed').insert(data).execute()
            print(f"Inserted post-PR closed responses for participant: {participant_id}, PR: {pr_url}")
        
        return {
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"Error saving post-PR closed responses: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error saving post-PR closed responses: {str(e)}"
        }


def save_end_study_responses(participant_id: str, responses: dict):
    """
    Save end-of-study responses to Supabase reviewer-end-study table.
    
    Args:
        participant_id: The participant's ID
        responses: Dictionary of all survey responses
        
    Returns:
        dict with 'success' and 'error' keys
    """
    if not supabase_client:
        return {
            'success': False,
            'error': 'Database client not initialized'
        }
    
    try:
        # Prepare data for insertion
        data = {
            'participant_id': participant_id,
            'workflow_comparison': responses.get('workflow_comparison') or responses.get('study_validation_description')
        }
        
        print(f"Prepared end-study data for participant {participant_id}: {data}")
        
        # Check if participant already has responses
        existing = supabase_client.table('reviewer-end-study').select('participant_id').eq('participant_id', participant_id).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            result = supabase_client.table('reviewer-end-study').update(data).eq('participant_id', participant_id).execute()
            print(f"Updated end-study responses for participant: {participant_id}")
        else:
            # Insert new record
            result = supabase_client.table('reviewer-end-study').insert(data).execute()
            print(f"Inserted end-study responses for participant: {participant_id}")
        
        return {
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"Error saving end-study responses: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error saving end-study responses: {str(e)}"
        }


def get_random_unassigned_pr(repository: str):
    """
    Get a random unassigned PR from completed issues in a repository.
    Looks for completed issues with PRs that haven't been assigned to reviewers yet.
    
    Args:
        repository: Repository in format "repository"
        
    Returns:
        dict with 'success', 'pr' (dict with url, number, title), and 'error' keys
    """
    if not supabase_client:
        return {
            'success': False,
            'error': 'Database client not initialized',
            'pr': None
        }
    
    try:
        
        repo_name = repository
        
        # Get all completed issues with PRs that haven't been assigned to reviewers yet
        # We'll check for issues that are completed (is_completed = true) and have a PR URL
        # but haven't been assigned to a reviewer (reviewer_assigned = false or null)
        
        # First, get all completed issues with PRs from contributor database
        contributor_client = get_contributor_supabase_client()
        if not contributor_client:
            return {
                'success': False,
                'error': 'Contributor database client not initialized',
                'pr': None
            }
        
        # Select all relevant fields from the repo-issues table
        response = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']).select(
            'repository, issue_url, issue_id, repository_id, is_assigned, is_completed, '
            'participant_id, participant_estimate, accepted_on, completed_on, pr_url, '
            'reviewer_assigned, reviewer_id, reviewer_assigned_on, reviewer_estimate, '
            'is_closed, is_merged, is_reviewed, using_ai, issue_sequence'
        ).eq('repository', repo_name).eq('is_completed', True).execute()
        
        print(f"Found {len(response.data) if response.data else 0} completed issues for {repository}")
        
        if not response.data or len(response.data) == 0:
            return {
                'success': False,
                'error': f"No completed issues found for repository {repository}",
                'pr': None
            }
        
        # Filter for issues that have PRs and haven't been assigned to reviewers
        available_issues = []
        for issue in response.data:
            # Check if this issue has a PR URL
            pr_url = issue.get('pr_url', '')
            if not pr_url or pr_url.strip() == '':
                continue
                
            # Check if this issue has already been assigned to a reviewer
            reviewer_assigned = issue.get('reviewer_assigned', False)
            if not reviewer_assigned:
                available_issues.append(issue)
        
        print(f"Found {len(available_issues)} available issues with PRs for review")
        
        if not available_issues:
            return {
                'success': False,
                'error': f"Sorry, please check back later! There are no more unassigned PRs in the repository {repository} right now.",
                'pr': None
            }
        
        # Randomly select one issue with PR
        import random
        selected_issue = random.choice(available_issues)
        
        # Extract all relevant information from the issue
        pr_url = selected_issue.get('pr_url', '')
        issue_url = selected_issue.get('issue_url', '')
        issue_id = selected_issue.get('issue_id', 'N/A')
        repository_id = selected_issue.get('repository_id', 'N/A')
        participant_id = selected_issue.get('participant_id', 'N/A')
        participant_estimate = selected_issue.get('participant_estimate', 'N/A')
        accepted_on = selected_issue.get('accepted_on', 'N/A')
        completed_on = selected_issue.get('completed_on', 'N/A')
        
        # Extract PR number from URL if possible
        pr_number = 'N/A'
        if pr_url and 'pull/' in pr_url:
            try:
                pr_number = pr_url.split('pull/')[-1].split('/')[0]
            except:
                pr_number = 'N/A'
        
        # Create a title from available information
        title = f"Issue #{issue_id}"
        if participant_estimate and participant_estimate != 'N/A':
            title += f" - {participant_estimate}"
        
        print(f"Retrieved issue {issue_id} with PR {pr_number} (not yet assigned to reviewer)")
        print(f"Issue URL: {issue_url}")
        print(f"PR URL: {pr_url}")
        
        return {
            'success': True,
            'pr': {
                'url': pr_url,  # PR URL
                'number': pr_number,
                'title': title,
                'repository': repo_name,
                'issue_id': issue_id,
                'issue_url': issue_url,  # Issue URL
                'repository_id': repository_id,
                'participant_id': participant_id,
                'participant_estimate': participant_estimate,
                'accepted_on': accepted_on,
                'completed_on': completed_on,
                'reviewer_estimate': selected_issue.get('reviewer_estimate'),
                'is_closed': selected_issue.get('is_closed'),
                'is_merged': selected_issue.get('is_merged'),
                'is_reviewed': selected_issue.get('is_reviewed'),
                'using_ai': selected_issue.get('using_ai'),
                'issue_sequence': selected_issue.get('issue_sequence')
            },
            'error': None
        }
        
    except Exception as e:
        print(f"Error getting random PR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error getting PR: {str(e)}",
            'pr': None
        }


def assign_pr_to_reviewer(reviewer_id: str, issue_id: int):
    """
    Assign a specific issue's PR to a reviewer by updating the repo-issues table.

    Args:
        reviewer_id: The reviewer's ID (e.g., "r1", "r2", etc.)
        issue_id: The issue ID whose PR should be assigned

    Returns:
        dict with 'success' and 'error' keys
    """
    contributor_client = get_contributor_supabase_client()
    if not contributor_client:
        print("ERROR: Contributor database client not initialized")
        return {
            'success': False,
            'error': 'Contributor database client not initialized'
        }

    try:
        print(f"=== STARTING PR ASSIGNMENT ===")
        print(f"Reviewer ID: {reviewer_id} (type: {type(reviewer_id)})")
        print(f"Issue ID: {issue_id} (type: {type(issue_id)})")

        # Update the issue to mark as assigned to reviewer with timestamp
        from datetime import datetime, timezone

        update_data = {
            'reviewer_assigned': True,
            'reviewer_id': reviewer_id,  # Store as string (r1, r2, etc.)
            'reviewer_assigned_on': datetime.now(timezone.utc).isoformat(),  # Current UTC timestamp
            'is_closed': False,
            'is_merged': False,
            'is_reviewed': False
        }

        print(f"Update data: {update_data}")
        print(f"Updating table 'repo-issues' where issue_id = {issue_id}")

        result = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']).update(update_data).eq('issue_id', issue_id).execute()

        print(f"Update result: {result}")

        if result.data and len(result.data) > 0:
            print(f"✅ Successfully assigned issue {issue_id} PR to reviewer {reviewer_id}")
            print(f"Updated row: {result.data[0]}")
            return {
                'success': True,
                'error': None
            }
        else:
            print(f"⚠️ Update returned empty data - issue may not exist or RLS policy blocked the update")
            return {
                'success': False,
                'error': f"Issue {issue_id} not found or RLS policy blocked the update. Check server logs."
            }

    except Exception as e:
        print(f"❌ ERROR assigning PR: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error assigning PR: {str(e)}"
        }


def get_assigned_pr_for_reviewer(reviewer_id: str, repository: str):
    """
    Load the PR assigned to a reviewer from the contributor repo-issues table.

    Args:
        reviewer_id: Reviewer's participant ID (e.g., r1)
        repository: repository string to scope the search

    Returns:
        dict with 'success', 'pr' (or None), and 'error'
    """
    contributor_client = get_contributor_supabase_client()
    if not contributor_client:
        return {
            'success': False,
            'error': 'Contributor database client not initialized',
            'pr': None
        }

    try:
        repo_name = repository

        response = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']).select(
            'repository, issue_url, issue_id, repository_id, pr_url, reviewer_assigned, reviewer_id, '
            'reviewer_estimate, new_contributor_estimate, reviewer_assigned_on, is_closed, is_merged, is_reviewed, '
            'using_ai, issue_sequence'
        ).eq('repository', repo_name).eq('reviewer_id', reviewer_id).eq('reviewer_assigned', True).limit(1).execute()

        if not response.data or len(response.data) == 0:
            return {'success': True, 'pr': None, 'error': None}

        issue = response.data[0]
        pr_url = issue.get('pr_url', '')
        issue_url = issue.get('issue_url', '')
        issue_id = issue.get('issue_id')
        pr_number = 'N/A'
        if pr_url and 'pull/' in pr_url:
            try:
                pr_number = pr_url.split('pull/')[-1].split('/')[0]
            except Exception:
                pr_number = 'N/A'

        title = f"Issue #{issue_id}"

        return {
            'success': True,
            'pr': {
                'url': pr_url,
                'number': pr_number,
                'title': title,
                'repository': repo_name,
                'issue_id': issue_id,
                'issue_url': issue_url,
                'reviewer_estimate': issue.get('reviewer_estimate'),
                'new_contributor_estimate': issue.get('new_contributor_estimate'),
                'is_closed': issue.get('is_closed'),
                'is_merged': issue.get('is_merged'),
                'is_reviewed': issue.get('is_reviewed')
            },
            'error': None
        }
    except Exception as e:
        print(f"Error loading assigned PR: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'pr': None, 'error': str(e)}


def list_assigned_prs_for_reviewer(reviewer_id: str, repository: str):
    """
    List all PRs assigned to a reviewer for a given repository.

    Args:
        reviewer_id: Reviewer's participant ID (e.g., r1)
        repository: repository string

    Returns:
        dict with 'success', 'prs' (list), and 'error'
    """
    contributor_client = get_contributor_supabase_client()
    if not contributor_client:
        return {
            'success': False,
            'error': 'Contributor database client not initialized',
            'prs': []
        }

    try:
        repo_name = repository

        response = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']).select(
            'repository, issue_url, issue_id, repository_id, pr_url, reviewer_assigned, reviewer_id, '
            'reviewer_estimate, new_contributor_estimate, reviewer_assigned_on, is_closed, is_merged, is_reviewed, '
            'using_ai, issue_sequence'
        ).eq('repository', repo_name).eq('reviewer_id', reviewer_id).eq('reviewer_assigned', True).execute()

        prs = []
        if response.data:
            for issue in response.data:
                pr_url = issue.get('pr_url', '')
                issue_url = issue.get('issue_url', '')
                issue_id = issue.get('issue_id')
                pr_number = 'N/A'
                if pr_url and 'pull/' in pr_url:
                    try:
                        pr_number = pr_url.split('pull/')[-1].split('/')[0]
                    except Exception:
                        pr_number = 'N/A'
                prs.append({
                    'url': pr_url,
                    'number': pr_number,
                    'title': f"Issue #{issue_id}",
                    'repository': repo_name,
                    'issue_id': issue_id,
                    'issue_url': issue_url,
                    'reviewer_estimate': issue.get('reviewer_estimate'),
                    'new_contributor_estimate': issue.get('new_contributor_estimate'),
                    'reviewer_assigned_on': issue.get('reviewer_assigned_on'),
                    'is_closed': issue.get('is_closed'),
                    'is_merged': issue.get('is_merged'),
                    'is_reviewed': issue.get('is_reviewed'),
                    'using_ai': issue.get('using_ai'),
                    'issue_sequence': issue.get('issue_sequence')
                })

        return {'success': True, 'prs': prs, 'error': None}

    except Exception as e:
        print(f"Error listing assigned PRs: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'prs': [], 'error': str(e)}

def get_participant_progress(participant_id: str):
    """
    Get the progress status of a reviewer participant.

    Args:
        participant_id: The participant's ID

    Returns:
        dict with 'success', 'progress' (dict with status info), and 'error' keys
    """
    if not supabase_client:
        return {
            'success': False,
            'error': 'Database client not initialized',
            'progress': None
        }

    try:

        # Check post-PR review responses
        post_pr_review_data = _safe_participant_query('reviewer-post-pr-review', participant_id)

        # Check post-PR closed responses
        post_pr_closed_data = _safe_participant_query('reviewer-post-pr-closed', participant_id)

        # Check end-study completion
        end_study_data = _safe_participant_query('reviewer-end-study', participant_id)

        progress = {
            'pre_study_completed': False,
            'post_pr_review_count': len(post_pr_review_data),
            'post_pr_closed_count': len(post_pr_closed_data),
            'end_study_completed': len(end_study_data) > 0,
            'post_pr_review_data': post_pr_review_data,
            'post_pr_closed_data': post_pr_closed_data,
            'end_study_data': end_study_data[0] if end_study_data else None
        }

        print(f"Progress for reviewer participant {participant_id}: {progress}")

        return {
            'success': True,
            'progress': progress,
            'error': None
        }

    except Exception as e:
        print(f"Error getting participant progress: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error getting progress: {str(e)}",
            'progress': None
        }


def check_nasa_tlx_completed(participant_id: str, pr_url: str):
    """
    Check if NASA TLX questions have been completed for a specific PR by querying Supabase.

    Args:
        participant_id: The participant's ID
        pr_url: The PR URL to check

    Returns:
        bool: True if NASA TLX questions are completed, False otherwise
    """
    if not supabase_client or not pr_url:
        print(f"[NASA TLX CHECK] Skipping check - client: {bool(supabase_client)}, pr_url: {pr_url}")
        return False

    try:
        # Normalize URL for comparison
        normalized_url = pr_url.strip().rstrip('/')
        print(f"[NASA TLX CHECK] Checking for participant {participant_id}, PR: {normalized_url}")

        # Query the database for this participant - get all entries to check URL matching
        response = supabase_client.table('reviewer-post-pr-review').select(
            'pr_url, nasa_tlx_mental_demand'
        ).eq('participant_id', participant_id).execute()

        print(f"[NASA TLX CHECK] Found {len(response.data) if response.data else 0} entries for participant")

        if response.data and len(response.data) > 0:
            # Find matching entry by normalized URL
            for entry in response.data:
                entry_url = entry.get('pr_url', '').strip().rstrip('/')
                if entry_url == normalized_url:
                    print(f"[NASA TLX CHECK] Found matching entry for PR")
                    value = entry.get('nasa_tlx_mental_demand')
                    if value and (not isinstance(value, str) or value.strip().lower() not in ['', 'not selected']):
                        print(f"[NASA TLX CHECK] Primary field complete - returning True")
                        return True
                    print(f"[NASA TLX CHECK] Primary field missing - returning False")
                    return False
        print(f"[NASA TLX CHECK] No matching entry found - returning False")
        return False
    except Exception as e:
        print(f"[NASA TLX CHECK] Error checking NASA TLX completion: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_code_quality_completed(participant_id: str, pr_url: str):
    """
    Check if code quality questions have been completed for a specific PR by querying Supabase.

    Args:
        participant_id: The participant's ID
        pr_url: The PR URL to check

    Returns:
        bool: True if code quality questions are completed, False otherwise
    """
    if not supabase_client or not pr_url:
        print(f"[CODE QUALITY CHECK] Skipping check - client: {bool(supabase_client)}, pr_url: {pr_url}")
        return False

    try:
        # Normalize URL for comparison
        normalized_url = pr_url.strip().rstrip('/')
        print(f"[CODE QUALITY CHECK] Checking for participant {participant_id}, PR: {normalized_url}")

        first_quality_key = next(iter(CODE_QUALITY_QUESTIONS.keys()))
        primary_field = f'code_quality_{first_quality_key}'
        response = supabase_client.table('reviewer-post-pr-review').select(
            f'pr_url, {primary_field}'
        ).eq('participant_id', participant_id).execute()

        print(f"[CODE QUALITY CHECK] Found {len(response.data) if response.data else 0} entries for participant")

        if response.data and len(response.data) > 0:
            # Find matching entry by normalized URL
            for entry in response.data:
                entry_url = entry.get('pr_url', '').strip().rstrip('/')
                if entry_url == normalized_url:
                    print(f"[CODE QUALITY CHECK] Found matching entry for PR")
                    value = entry.get(primary_field)
                    if value and (not isinstance(value, str) or value.strip().lower() not in ['', 'not selected']):
                        print(f"[CODE QUALITY CHECK] Primary field complete - returning True")
                        return True
                    print(f"[CODE QUALITY CHECK] Primary field missing - returning False")
                    return False
        print(f"[CODE QUALITY CHECK] No matching entry found - returning False")
        return False
    except Exception as e:
        print(f"[CODE QUALITY CHECK] Error checking code quality completion: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_ai_detection_completed(participant_id: str, pr_url: str):
    """
    Check if AI detection questions have been completed for a specific PR by querying Supabase.

    Args:
        participant_id: The participant's ID
        pr_url: The PR URL to check

    Returns:
        bool: True if AI detection questions are completed, False otherwise
    """
    if not supabase_client or not pr_url:
        print(f"[AI DETECTION CHECK] Skipping check - client: {bool(supabase_client)}, pr_url: {pr_url}")
        return False

    try:
        # Normalize URL for comparison
        normalized_url = pr_url.strip().rstrip('/')
        print(f"[AI DETECTION CHECK] Checking for participant {participant_id}, PR: {normalized_url}")

        # Query the database for this participant - get all entries to check URL matching
        response = supabase_client.table('reviewer-post-pr-review').select(
            'pr_url, ai_likelihood'
        ).eq('participant_id', participant_id).execute()

        print(f"[AI DETECTION CHECK] Found {len(response.data) if response.data else 0} entries for participant")

        if response.data and len(response.data) > 0:
            # Find matching entry by normalized URL
            for entry in response.data:
                entry_url = entry.get('pr_url', '').strip().rstrip('/')
                if entry_url == normalized_url:
                    print(f"[AI DETECTION CHECK] Found matching entry for PR")
                    value = entry.get('ai_likelihood')
                    if value and (not isinstance(value, str) or value.strip() != ''):
                        print(f"[AI DETECTION CHECK] Primary field complete - returning True")
                        return True
                    print(f"[AI DETECTION CHECK] Primary field missing - returning False")
                    return False
        print(f"[AI DETECTION CHECK] No matching entry found - returning False")
        return False
    except Exception as e:
        print(f"[AI DETECTION CHECK] Error checking AI detection completion: {e}")
        import traceback
        traceback.print_exc()
        return False


def determine_current_page(participant_id: str, survey_responses: dict = None):
    """
    Determine the appropriate page for a participant based on their completion status.

    Args:
        participant_id: The participant's ID
        survey_responses: Optional dict of survey responses from session state

    Returns:
        int: The page number the participant should be on

    Page mapping (new flow):
        0: participant_id_page - Participant ID entry
        2: setup_checklist_page - Reviewer setup checklist
        3: pr_assignment_page - PR assignment and time estimates
        4: review_submission_page - Confirm first review submitted
        5: nasa_tlx_questions_page - NASA-TLX workload questions
        6: code_quality_ratings_page - Code quality ratings
        7: ai_detection_page - AI detection questions
        8: pr_status_page - PR status check (can request another PR)
        9: collaboration_questions_page - Collaboration questions (if PR closed/merged)
        10: contributor_perception_page - Contributor perception questions
        11: study_validation_page - Study validation
        12: completion_page - Survey completion
    """
    if not participant_id:
        return 0  # No participant ID, start at beginning

    try:
        # Get repository assignment
        repo_result = get_repository_assignment(participant_id)
        if not repo_result['success']:
            return 0  # No valid repository assignment

        assigned_repo = repo_result['repository']

        # Require setup checklist completion before proceeding to PR assignment
        # BUT skip checklist requirement if they've already completed a review
        setup_complete = False
        if isinstance(survey_responses, dict):
            setup_complete = survey_responses.get('setup_checklist_complete', False)

        # Check if they've already started reviewing (completed at least one review)
        progress_result = get_participant_progress(participant_id)
        has_started_reviews = False
        if progress_result.get('success') and progress_result.get('progress'):
            has_started_reviews = progress_result['progress'].get('post_pr_review_count', 0) > 0

        if not setup_complete and not has_started_reviews:
            return 2

        # Check if PR is assigned and if estimates are provided
        pr_result = get_assigned_pr_for_reviewer(participant_id, assigned_repo)
        if not pr_result['success'] or pr_result['pr'] is None:
            return 3  # No PR assigned yet, go to PR assignment page

        pr_data = pr_result['pr']
        session_responses = survey_responses if isinstance(survey_responses, dict) else {}
        reviewer_estimate = pr_data.get('reviewer_estimate')
        new_contributor_estimate = pr_data.get('new_contributor_estimate')
        has_estimates = bool(reviewer_estimate and new_contributor_estimate)

        print(f"[DEBUG] PR data: reviewer_estimate={reviewer_estimate}, new_contributor_estimate={new_contributor_estimate}, has_estimates={has_estimates}")

        if not has_estimates:
            print(f"[DEBUG] No estimates found, directing to page 3")
            return 3  # PR assigned but no estimates, go to PR assignment page

        # Check if initial review has been submitted (is_reviewed flag or survey response)
        # Also consider PR merged/closed as evidence of review completion
        is_reviewed = pr_data.get('is_reviewed')
        is_closed = pr_data.get('is_closed')
        is_merged = pr_data.get('is_merged')
        if session_responses.get('is_reviewed') == "Yes - I've submitted my review":
            is_reviewed = True
        # If PR is already merged or closed, they must have reviewed it
        if is_merged or is_closed:
            is_reviewed = True
        print(f"[DEBUG] Estimates found, checking is_reviewed={is_reviewed}, is_merged={is_merged}, is_closed={is_closed}")
        if not is_reviewed:
            print(f"[DEBUG] Review not submitted, directing to page 4")
            return 4  # Estimates provided but review not submitted, go to review submission page

        # Get progress data
        progress_result = get_participant_progress(participant_id)
        if not progress_result['success']:
            return 5  # Error getting progress, start with NASA-TLX questions

        progress = progress_result.get('progress') or {}
        completed_pr_reviews = progress.get('post_pr_review_count', 0)
        closed_pr_reviews = progress.get('post_pr_closed_count', 0)
        post_pr_review_entries = progress.get('post_pr_review_data') or []
        current_pr_url = pr_data.get('url')
        all_reviewed_prs_closed = (
            closed_pr_reviews >= completed_pr_reviews and completed_pr_reviews > 0
        )

        def normalize_url(url: str) -> str:
            if not url:
                return ''
            return url.strip().rstrip('/')

        def find_post_pr_entry(entries, pr_url):
            if not pr_url:
                return None
            normalized_target = normalize_url(pr_url)
            for entry in entries:
                entry_url = normalize_url(entry.get('pr_url'))
                if entry_url and entry_url == normalized_target:
                    return entry
            return None

        def is_valid_response(value):
            if value is None:
                return False
            if isinstance(value, str):
                stripped = value.strip()
                if not stripped or stripped.lower() == "not selected":
                    return False
            return True

        def has_answers(entry, keys, prefix=""):
            if not entry or not isinstance(entry, dict):
                return False
            for key in keys:
                column = f"{prefix}{key}" if prefix else key
                value = entry.get(column)
                if not is_valid_response(value):
                    return False
            return True

        def collect_sources(*sources):
            return [source for source in sources if isinstance(source, dict)]

        def get_nested_dict(source, key):
            if isinstance(source, dict):
                value = source.get(key)
                if isinstance(value, dict):
                    return value
            return None

        def sources_have_answers(sources, keys, prefix=""):
            for source in sources:
                if has_answers(source, keys, prefix=prefix):
                    return True
            return False

        current_post_pr_entry = find_post_pr_entry(post_pr_review_entries, current_pr_url)
        if not current_post_pr_entry and (not current_pr_url or current_pr_url in ('', 'N/A')):
            # Fallback: if no PR URL is available, use the most recent entry
            if post_pr_review_entries:
                current_post_pr_entry = sorted(
                    post_pr_review_entries,
                    key=lambda e: e.get('updated_at') or e.get('created_at') or '',
                    reverse=True
                )[0]

        session_assigned_pr = session_responses.get('assigned_pr') if session_responses else None
        shared_sources = collect_sources(current_post_pr_entry, pr_data, session_assigned_pr, session_responses)

        review_quota_met = completed_pr_reviews >= MIN_COMPLETED_REVIEWS
        artifact_status_map = session_responses.get('artifact_upload_status', {}) if isinstance(session_responses, dict) else {}
        issue_key = str(pr_data.get('issue_id') or pr_data.get('url') or 'current_pr')
        artifact_complete = artifact_status_map.get(issue_key, False)

        # Check NASA TLX completion directly from database
        nasa_complete = check_nasa_tlx_completed(participant_id, current_pr_url)
        print(f"[DEBUG] NASA TLX completed from database: {nasa_complete}")
        if not nasa_complete:
            return 5  # NASA-TLX questions incomplete for this PR

        # Check code quality completion directly from database
        code_quality_complete = check_code_quality_completed(participant_id, current_pr_url)
        print(f"[DEBUG] Code quality completed from database: {code_quality_complete}")
        if not code_quality_complete:
            return 6  # Code quality ratings incomplete

        # Check AI detection completion directly from database
        ai_detection_complete = check_ai_detection_completed(participant_id, current_pr_url)
        print(f"[DEBUG] AI detection completed from database: {ai_detection_complete}")
        if not ai_detection_complete:
            return 7  # AI detection questions incomplete

        if review_quota_met:
            print(
                f"[DEBUG] Reviewer quota met ({completed_pr_reviews}/{MIN_COMPLETED_REVIEWS}). Proceeding to end-of-study checks."
            )
            if not all_reviewed_prs_closed:
                print(
                    f"[DEBUG] Reviewer still has open PRs ({closed_pr_reviews}/{completed_pr_reviews}). Redirecting to PR status page."
                )
                return 8
            if not artifact_complete:
                print(f"[DEBUG] Awaiting artifact uploads for issue_key={issue_key}.")
                return 11
            if not progress.get('end_study_completed'):
                return 12  # Go directly to study validation
            return 13  # Completion page once validation done

        # After post-PR review questions, go to PR status page
        # Check if PR is closed/merged
        if not is_closed and not is_merged:
            return 8  # PR not closed yet, go to PR status page

        # Check post-PR closed completion
        if progress.get('post_pr_closed_count', 0) == 0:
            return 9  # PR closed but no post-PR closed data, go to collaboration questions

        if not artifact_complete:
            print(f"[DEBUG] Awaiting artifact uploads for issue_key={issue_key}.")
            return 11

        # Ensure minimum number of PR reviews before end-of-study
        if completed_pr_reviews < MIN_COMPLETED_REVIEWS:
            print(
                f"[DEBUG] Completed PR reviews {completed_pr_reviews}/{MIN_COMPLETED_REVIEWS}. Redirecting to PR status page."
            )
            return 8  # Need to complete additional PR reviews

        # Check end-study completion
        if not progress.get('end_study_completed'):
            return 12  # Post-PR closed complete, go to study validation

        if closed_pr_reviews < completed_pr_reviews:
            print(
                f"[DEBUG] Cannot finish - pending PR closures ({closed_pr_reviews}/{completed_pr_reviews}). Redirecting to PR status page."
            )
            return 8

        return 13  # Go to completion page

    except Exception as e:
        print(f"Error determining current page: {e}")
        import traceback
        traceback.print_exc()
        return 0  # Default to start on error


def save_reviewer_estimate_for_issue(issue_id: int, reviewer_estimate: str, new_contributor_estimate: str):
    """
    Save the reviewer's pre-review time estimate to the contributor project's repo-issues table.

    Args:
        issue_id: The issue ID in the contributor repo-issues table
        reviewer_estimate: One of the reviewer estimate options
        new_contributor_estimate: estimate for a new contributor completing the PR

    Returns:
        dict with 'success' and 'error' keys
    """
    contributor_client = get_contributor_supabase_client()
    if not contributor_client:
        return {
            'success': False,
            'error': 'Contributor database client not initialized'
        }

    try:
        update_fields = {'reviewer_estimate': reviewer_estimate}
        if new_contributor_estimate:
            update_fields['new_contributor_estimate'] = new_contributor_estimate

        result = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']) \
            .update(update_fields) \
            .eq('issue_id', issue_id) \
            .execute()

        if result.data and len(result.data) > 0:
            return {
                'success': True,
                'error': None
            }
        else:
            return {
                'success': False,
                'error': f"Issue {issue_id} not found or update blocked by RLS."
            }
    except Exception as e:
        return {
            'success': False,
            'error': f"Error saving reviewer estimate: {str(e)}"
        }


def save_session_state(participant_id: str, current_page: int, survey_responses: dict):
    """
    Save the current session state to the reviewer-sessions table.
    
    Args:
        participant_id: The participant's ID
        current_page: Current page number
        survey_responses: Dictionary of all survey responses
        
    Returns:
        dict with 'success' and 'error' keys
    """
    if not supabase_client:
        return {
            'success': False,
            'error': 'Database client not initialized'
        }
    
    try:
        from datetime import datetime, timezone
        
        # Create session ID from participant ID and timestamp
        session_id = f"{participant_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare data for insertion/update (match reviewer-sessions schema)
        data = {
            'session_id': session_id,
            'participant_id': participant_id,
            'current_page': str(current_page),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Check if participant already has a session
        existing = supabase_client.table('reviewer-sessions').select('session_id').eq('participant_id', participant_id).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing session
            result = supabase_client.table('reviewer-sessions').update(data).eq('participant_id', participant_id).execute()
            print(f"Updated session for participant: {participant_id}, page: {current_page}")
        else:
            # Insert new session
            data['started_at'] = datetime.now(timezone.utc).isoformat()
            data['created_at'] = datetime.now(timezone.utc).isoformat()
            result = supabase_client.table('reviewer-sessions').insert(data).execute()
            print(f"Created new session for participant: {participant_id}, page: {current_page}")
        
        return {
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"Error saving session state: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error saving session state: {str(e)}"
        }


def load_session_state(participant_id: str):
    """
    Load the saved session state for a participant.
    
    Args:
        participant_id: The participant's ID
        
    Returns:
        dict with 'success', 'current_page', 'survey_responses', and 'error' keys
    """
    if not supabase_client:
        return {
            'success': False,
            'error': 'Database client not initialized',
            'current_page': 0,
            'survey_responses': {}
        }
    
    try:
        # Get the most recent session for this participant
        response = supabase_client.table('reviewer-sessions').select('*').eq('participant_id', participant_id).order('updated_at', desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            session = response.data[0]
            current_page = int(session.get('current_page', 0))
            
            # No survey_responses column in reviewer-sessions schema
            # Provide participant_id in responses so pages relying on it can resume smoothly
            survey_responses = {'participant_id': participant_id}
            
            print(f"Loaded session for participant: {participant_id}, page: {current_page}")
            return {
                'success': True,
                'current_page': current_page,
                'survey_responses': survey_responses,
                'error': None
            }
        else:
            return {
                'success': True,
                'current_page': 0,
                'survey_responses': {},
                'error': None
            }
            
    except Exception as e:
        print(f"Error loading session state: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error loading session state: {str(e)}",
            'current_page': 0,
            'survey_responses': {}
        }
