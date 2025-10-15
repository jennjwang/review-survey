# Reviewer Survey

This is a Streamlit-based survey application for collecting data from code reviewers participating in a study about the impact of AI on developer productivity.

## Survey Structure

The survey is organized into several sections:

### Pre-Study (Pages 0-4)

- **Consent** (Page 0): Study introduction and consent
- **Participant ID** (Page 1): Participant identification
- **Developer Experience** (Page 2): Professional development experience
- **Codebase Experience** (Page 3): Experience with the specific codebase
- **Pre-Study Complete** (Page 4): Pre-study completion confirmation

### Post-PR-Review (Pages 5-7)

- **NASA-TLX Questions** (Page 5): Workload assessment using NASA-TLX scale
- **Code Quality Ratings** (Page 6): Code quality assessment on multiple dimensions
- **AI Detection** (Page 7): Assessment of whether PR contains AI-generated code

### Post-PR-Closed (Pages 8-9)

- **Collaboration Questions** (Page 8): Assessment of collaboration with contributor
- **Contributor Perception** (Page 9): Perception of contributor after PR discussion

### End of Study (Page 10)

- **Workflow Comparison** (Page 10): Comparison with normal reviewing workflow

### Completion (Pages 11-12)

- **Survey Complete** (Page 11): Survey completion confirmation
- **Thank You** (Page 12): Final thank you page

## Questions Included

### Pre-Study Questions

1. **Professional Experience**: Years of professional development experience
2. **Occupation Description**: Brief description of current work
3. **Codebase Experience**: Lines of code written/modified in the codebase

### Post-PR-Review Questions

1. **NASA-TLX Workload Assessment**:

   - Mental demand
   - Physical demand (effort required)
   - Frustration/stress level

2. **Code Quality Ratings** (1-5 scale):

   - Readability
   - Analyzability
   - Modifiability
   - Testability
   - Stability
   - Correctness
   - Compliance with standards

3. **AI Detection**:
   - Likelihood of AI-generated code (1-5 scale)
   - Reasoning for the assessment (open-ended)

### Post-PR-Closed Questions

1. **Collaboration Assessment** (1-5 scale):

   - Psychological safety
   - Constructiveness
   - Shared ownership
   - Collaborative problem-solving

2. **Contributor Perception** (1-5 scale):

   - Capability
   - Trustworthiness
   - Friendliness
   - Intelligence

3. **Open-ended Questions**:
   - Overall collaboration description
   - Impact on contributor perception

### End of Study Questions

1. **Workflow Comparison**: How the study workflow compared to normal responsibilities

## Running the Survey

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the survey:

   ```bash
   streamlit run main.py
   ```

3. Access the survey in your browser at the provided URL (typically `http://localhost:8501`)

## Features

- **Responsive Design**: Clean, professional interface optimized for survey completion
- **Progress Tracking**: Session state maintains responses across pages
- **Validation**: Required field validation before proceeding
- **Navigation**: Back/Next buttons with proper state management
- **PR Context**: Display of PR information when available
- **Consistent Styling**: Unified look and feel across all pages

## File Structure

```
reviewer/
├── main.py                    # Main application entry point
├── survey_questions.py        # Question definitions and scales
├── survey_components.py       # Reusable UI components
├── survey_utils.py           # Utility functions
├── styles.py                 # CSS styling
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── pages/                    # Page modules organized by section
    ├── __init__.py
    ├── pre_study/
    ├── post_pr_review/
    ├── post_pr_closed/
    ├── end_study/
    └── completion/
```

## Customization

To modify questions or add new pages:

1. **Add new questions**: Update `survey_questions.py` with new question definitions
2. **Create new pages**: Add new page modules in the appropriate section directory
3. **Update navigation**: Modify the `page_routes` dictionary in `main.py`
4. **Update imports**: Add new page imports to the relevant `__init__.py` files

## Data Collection

Survey responses are stored in `st.session_state['survey_responses']` and can be:

- Displayed in the completion page for user review
- Exported to external systems
- Saved to databases
- Processed for analysis

The survey is designed to be integrated with data collection systems as needed for the research study.
# review-survey
