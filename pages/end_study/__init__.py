"""
End-of-study pages for the reviewer survey.
"""

from .study_validation import study_validation_page
from .completion import completion_page

__all__ = [
    'study_validation_page',
    'completion_page'
]
