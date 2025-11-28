"""
End-of-study pages for the reviewer survey.
"""

from .end_pr_reviews import end_pr_reviews_page
from .study_validation import study_validation_page
from .completion import completion_page

__all__ = [
    'end_pr_reviews_page',
    'study_validation_page',
    'completion_page'
]
