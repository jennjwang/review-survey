"""
Post-PR-Closed pages for the reviewer survey.
"""

from .collaboration_questions import collaboration_questions_page
from .contributor_perception import contributor_perception_page
from .pr_status import pr_status_page

__all__ = [
    'collaboration_questions_page',
    'contributor_perception_page',
    'pr_status_page'
]
