"""
Survey pages package for reviewer survey.
Organized into logical sections: pre-study, post-pr-review, post-pr-closed, and end-study.
"""

# Import from organized sections
from .pre_study import (
    participant_id_page,
    developer_experience_page,
    codebase_experience_page,
    pr_assignment_page
)

from .post_pr_review import (
    nasa_tlx_questions_page,
    code_quality_ratings_page,
    ai_detection_page,
    pr_status_page,
    review_submission_page
)

from .post_pr_closed import (
    collaboration_questions_page,
    contributor_perception_page,
    closure_confirmation_page
)

from .end_study import (
    workflow_comparison_page,
    study_validation_page
)

from .completion import (
    completion_page
)

__all__ = [
    # Pre-study pages
    'participant_id_page',
    'developer_experience_page',
    'codebase_experience_page',
    'pr_assignment_page',
    
    # Post-PR-Review pages
    'nasa_tlx_questions_page',
    'code_quality_ratings_page',
    'ai_detection_page',
    'pr_status_page',
    'review_submission_page',
    
    # Post-PR-Closed pages
    'collaboration_questions_page',
    'contributor_perception_page',
    'closure_confirmation_page',
    
    # End of study pages
    'workflow_comparison_page',
    'study_validation_page',
    
    # Completion pages
    'completion_page'
]
