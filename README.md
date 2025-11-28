# Reviewer Survey

This is a Streamlit-based survey application for collecting data from code reviewers participating in a study about the impact of AI on developer productivity.

## Survey Structure

The survey is organized into several sections:

### Pre-Study (Pages 0-4)

- **Consent** (Page 0): Study introduction and consent
- **Participant ID** (Page 1): Participant identification
- **PR Assignment** (Page 3): Assign and confirm the study PR
- **Pre-Study Complete** (Page 4): Pre-study completion confirmation

### Post-PR-Review (Pages 5-7)

- **NASA-TLX Questions** (Page 5): Workload assessment using NASA-TLX scale
- **Code Quality Ratings** (Page 6): Code quality assessment on multiple dimensions
- **AI Detection** (Page 7): Assessment of whether PR contains AI-generated code

### Post-PR-Closed (Pages 8-9)

- **Collaboration Questions** (Page 8): Assessment of collaboration with contributor
- **Contributor Perception** (Page 9): Perception of contributor after PR discussion

Participants repeat the PR-review cycle (Pages 5-10) until they have completed **at least four** PR reviews. All reviewed PRs must be merged or closed (with the collaboration/perception questionnaire submitted) before the study can be finalized.

### End of Study (Page 11)

- **Study Validation** (Page 11): Reflection on how the study workflow compares to normal responsibilities

### Completion (Page 12)

- **Survey Complete** (Page 12): Final thank you page and study contact information

## Questions Included

### Pre-Study Questions

The pre-study section now focuses solely on verifying participant information and confirming the assigned PR.

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

1. **Study Validation**: How the study workflow compared to normal responsibilities once the minimum (four) PR reviews are complete

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
    └── end_study/            # Includes end-of-study + completion pages
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

### Contributor Repo Schema

The reviewer workflow interacts with the contributor-owned `repo-issues` table (hosted in Supabase). The table now includes the following key fields that the survey code expects:

- `reviewer_assigned`, `is_assigned`, `reviewer_id`, `reviewer_assigned_on`: track which reviewer currently owns the PR.
- `reviewer_estimate`, `is_closed`, `is_merged`, `is_reviewed`: store reviewer-specific metadata and status updates written from the survey.
- `using_ai`, `issue_sequence`: additional contributor signals now surfaced when selecting or displaying PR assignments.

Make sure these columns exist in the contributor database before running the updated survey stack.
# review-survey
