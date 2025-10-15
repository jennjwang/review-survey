"""
Data layer for reviewer survey database operations.
"""

from supabase import create_client
from contributor_config import get_contributor_db_creds, CONTRIBUTOR_TABLES


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


def get_repository_assignment(participant_id: str):
    """
    Get repository assignment for a reviewer participant.
    
    Args:
        participant_id: The participant's ID
        
    Returns:
        dict with 'success', 'repository' (formatted as owner/name), 'url', and 'error' keys
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
            owner = row.get('repository_owner')
            repository_name = row.get('repository_name')
            repository_url = row.get('repository_url')
            
            print(f"Owner: {owner}")
            print(f"Repository name: {repository_name}")
            print(f"Repository URL: {repository_url}")
            
            if owner and repository_name:
                return {
                    'success': True,
                    'repository': f"{owner}/{repository_name}",
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


def save_pre_study_responses(participant_id: str, responses: dict):
    """
    Save pre-study survey responses to Supabase reviewer-pre-study table.
    
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
            'professional_experience': responses.get('professional_experience'),
            'occupation_description': responses.get('occupation_description'),
            'codebase_experience': responses.get('codebase_experience'),
        }
        
        print(f"Prepared pre-study data for participant {participant_id}: {data}")
        
        # Check if participant already has responses
        existing = supabase_client.table('reviewer-pre-study').select('participant_id').eq('participant_id', participant_id).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            result = supabase_client.table('reviewer-pre-study').update(data).eq('participant_id', participant_id).execute()
            print(f"Updated pre-study responses for participant: {participant_id}")
        else:
            # Insert new record
            result = supabase_client.table('reviewer-pre-study').insert(data).execute()
            print(f"Inserted pre-study responses for participant: {participant_id}")
        
        return {
            'success': True,
            'error': None
        }
        
    except Exception as e:
        print(f"Error saving pre-study responses: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f"Error saving pre-study responses: {str(e)}"
        }


def save_post_pr_review_responses(participant_id: str, pr_number: str, pr_title: str, pr_url: str, responses: dict):
    """
    Save post-PR review responses to Supabase reviewer-post-pr-review table.
    
    Args:
        participant_id: The participant's ID
        pr_number: The PR number
        pr_title: The PR title
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
        # Prepare data for insertion
        data = {
            'participant_id': participant_id,
            'pr_number': pr_number,
            'pr_title': pr_title,
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
        
        print(f"Prepared post-PR review data for participant {participant_id}: {data}")
        
        # Check if participant already has responses for this PR
        existing = supabase_client.table('reviewer-post-pr-review').select('participant_id').eq('participant_id', participant_id).eq('pr_number', pr_number).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            result = supabase_client.table('reviewer-post-pr-review').update(data).eq('participant_id', participant_id).eq('pr_number', pr_number).execute()
            print(f"Updated post-PR review responses for participant: {participant_id}, PR: {pr_number}")
        else:
            # Insert new record
            result = supabase_client.table('reviewer-post-pr-review').insert(data).execute()
            print(f"Inserted post-PR review responses for participant: {participant_id}, PR: {pr_number}")
        
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


def save_post_pr_closed_responses(participant_id: str, pr_number: str, pr_title: str, pr_url: str, responses: dict):
    """
    Save post-PR closed responses to Supabase reviewer-post-pr-closed table.
    
    Args:
        participant_id: The participant's ID
        pr_number: The PR number
        pr_title: The PR title
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
        # Prepare data for insertion
        data = {
            'participant_id': participant_id,
            'pr_number': pr_number,
            'pr_title': pr_title,
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
        
        print(f"Prepared post-PR closed data for participant {participant_id}: {data}")
        
        # Check if participant already has responses for this PR
        existing = supabase_client.table('reviewer-post-pr-closed').select('participant_id').eq('participant_id', participant_id).eq('pr_number', pr_number).execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing record
            result = supabase_client.table('reviewer-post-pr-closed').update(data).eq('participant_id', participant_id).eq('pr_number', pr_number).execute()
            print(f"Updated post-PR closed responses for participant: {participant_id}, PR: {pr_number}")
        else:
            # Insert new record
            result = supabase_client.table('reviewer-post-pr-closed').insert(data).execute()
            print(f"Inserted post-PR closed responses for participant: {participant_id}, PR: {pr_number}")
        
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
        repository: Repository in format "owner/repository"
        
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
        # Parse repository
        if '/' not in repository:
            return {
                'success': False,
                'error': 'Invalid repository format',
                'pr': None
            }
        
        owner, repo_name = repository.split('/', 1)
        
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
            'owner, repository, issue_url, issue_id, repository_id, is_assigned, is_completed, '
            'participant_id, participant_estimate, accepted_on, completed_on, pr_url, '
            'reviewer_assigned, reviewer_id, reviewer_assigned_on'
        ).eq('owner', owner).eq('repository', repo_name).eq('is_completed', True).execute()
        
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
                'error': f"No unassigned PRs available for review in repository {repository}",
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
                'owner': owner,
                'repository': repo_name,
                'issue_id': issue_id,
                'issue_url': issue_url,  # Issue URL
                'repository_id': repository_id,
                'participant_id': participant_id,
                'participant_estimate': participant_estimate,
                'accepted_on': accepted_on,
                'completed_on': completed_on
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
            'reviewer_assigned_on': datetime.now(timezone.utc).isoformat()  # Current UTC timestamp
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
        repository: owner/repo string to scope the search

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
        if '/' not in repository:
            return {'success': False, 'error': 'Invalid repository format', 'pr': None}
        owner, repo_name = repository.split('/', 1)

        response = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']).select(
            'owner, repository, issue_url, issue_id, repository_id, pr_url, reviewer_assigned, reviewer_id'
        ).eq('owner', owner).eq('repository', repo_name).eq('reviewer_id', reviewer_id).eq('reviewer_assigned', True).limit(1).execute()

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
                'owner': owner,
                'repository': repo_name,
                'issue_id': issue_id,
                'issue_url': issue_url
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
        repository: owner/repo string

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
        if '/' not in repository:
            return {'success': False, 'error': 'Invalid repository format', 'prs': []}
        owner, repo_name = repository.split('/', 1)

        response = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']).select(
            'owner, repository, issue_url, issue_id, repository_id, pr_url, reviewer_assigned, reviewer_id'
        ).eq('owner', owner).eq('repository', repo_name).eq('reviewer_id', reviewer_id).eq('reviewer_assigned', True).execute()

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
                    'owner': owner,
                    'repository': repo_name,
                    'issue_id': issue_id,
                    'issue_url': issue_url
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
        # Check pre-study completion
        pre_study = supabase_client.table('reviewer-pre-study').select('*').eq('participant_id', participant_id).execute()
        
        # Check post-PR review responses
        post_pr_review = supabase_client.table('reviewer-post-pr-review').select('*').eq('participant_id', participant_id).execute()
        
        # Check post-PR closed responses
        post_pr_closed = supabase_client.table('reviewer-post-pr-closed').select('*').eq('participant_id', participant_id).execute()
        
        # Check end-study completion
        end_study = supabase_client.table('reviewer-end-study').select('*').eq('participant_id', participant_id).execute()
        
        progress = {
            'pre_study_completed': len(pre_study.data) > 0 if pre_study.data else False,
            'post_pr_review_count': len(post_pr_review.data) if post_pr_review.data else 0,
            'post_pr_closed_count': len(post_pr_closed.data) if post_pr_closed.data else 0,
            'end_study_completed': len(end_study.data) > 0 if end_study.data else False,
            'pre_study_data': pre_study.data[0] if pre_study.data and len(pre_study.data) > 0 else None,
            'post_pr_review_data': post_pr_review.data if post_pr_review.data else [],
            'post_pr_closed_data': post_pr_closed.data if post_pr_closed.data else [],
            'end_study_data': end_study.data[0] if end_study.data and len(end_study.data) > 0 else None
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


def save_reviewer_estimate_for_issue(issue_id: int, reviewer_estimate: str):
    """
    Save the reviewer's pre-review time estimate to the contributor project's repo-issues table.

    Args:
        issue_id: The issue ID in the contributor repo-issues table
        reviewer_estimate: One of the ESTIMATE_OPTIONS strings

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
        result = contributor_client.table(CONTRIBUTOR_TABLES['repo_issues']) \
            .update({'reviewer_estimate': reviewer_estimate}) \
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
