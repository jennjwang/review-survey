"""
Post-PR-Closed pages for the reviewer survey.
"""

from .collaboration_questions import collaboration_questions_page
from .contributor_perception import contributor_perception_page
from .closure_confirmation import closure_confirmation_page

__all__ = [
    'collaboration_questions_page',
    'contributor_perception_page',
    'closure_confirmation_page'
]
