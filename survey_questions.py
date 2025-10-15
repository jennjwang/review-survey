"""
Survey questions and configuration data for the reviewer survey.
"""

# Professional experience options
EXPERIENCE_OPTIONS = (
    "Less than 1 year",
    "1–3 years",
    "4–6 years",
    "7–10 years",
    "More than 10 years"
)

# Codebase experience options
CODEBASE_EXPERIENCE_OPTIONS = [
    "Fewer than 100",
    "100–1,000",
    "1,001–10,000",
    "10,001–50,000",
    "More than 50,000"
]

# NASA-TLX scale options (1-7)
NASA_TLX_SCALE = [1, 2, 3, 4, 5, 6, 7]

# NASA-TLX questions
NASA_TLX_QUESTIONS = {
    'mental_demand': 'How mentally demanding was the task?',
    'physical_demand': 'How hard did you have to work to accomplish your level of performance?',
    'frustration': 'How frustrated, annoyed, or stressed did you feel while reviewing this PR?'
}

# Code quality rating scale (1-5)
QUALITY_SCALE = [1, 2, 3, 4, 5]

# Code quality questions
CODE_QUALITY_QUESTIONS = {
    'readability': 'This code is easy to read (readability)',
    'analyzability': 'This code\'s logic and structure are easy to understand (analyzability)',
    'modifiability': 'This code would be easy to modify or extend (modifiability)',
    'testability': 'This code would be easy to test (testability)',
    'stability': 'This code would be stable when changes are made (stability)',
    'correctness': 'This code performs as intended (correctness)',
    'compliance': 'This code follows the repository\'s established standards and practices (compliance)'
}

# AI detection scale (1-5)
AI_DETECTION_SCALE = [1, 2, 3, 4, 5]

# AI detection questions
AI_DETECTION_QUESTIONS = {
    'ai_likelihood': 'How likely is it that this PR included AI-generated code?',
    'ai_reasoning': 'What made you think this PR did or did not contain AI-generated code?'
}

# Collaboration rating scale (1-5)
COLLABORATION_SCALE = [1, 2, 3, 4, 5]

# Collaboration questions
COLLABORATION_QUESTIONS = {
    'psychological_safety': 'I felt that my feedback was respected by the contributor (psychological safety)',
    'constructiveness': 'Contributors engaged in discussions in a constructive way (constructiveness)',
    'shared_ownership': 'I felt a shared sense of responsibility with the contributor for improving the code during reviews (shared ownership)',
    'collaborative_problem_solving': 'The contributor engaged in productive discussions about code design (collaborative problem-solving)'
}

# Contributor perception scale (1-5)
PERCEPTION_SCALE = [1, 2, 3, 4, 5]

# Contributor perception questions
PERCEPTION_QUESTIONS = {
    'capable': 'I see this contributor as capable',
    'trustworthy': 'I see this contributor as trustworthy',
    'friendly': 'I see this contributor as friendly',
    'intelligent': 'I see this contributor as intelligent'
}

# Scale labels for display
SCALE_LABELS = {
    'nasa_tlx': {
        1: 'Very low',
        7: 'Very high'
    },
    'quality': {
        1: 'Strongly disagree',
        5: 'Strongly agree'
    },
    'ai_detection': {
        1: 'Definitely not',
        5: 'Definitely yes'
    },
    'collaboration': {
        1: 'Strongly disagree',
        5: 'Strongly agree'
    },
    'perception': {
        1: 'Strongly disagree',
        5: 'Strongly agree'
    }
}
