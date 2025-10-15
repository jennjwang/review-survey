"""
Centralized CSS styles for the reviewer survey application.
Uses sustainable styling approaches that won't break with Streamlit updates.

APPROACH:
- Use stable selectors (data attributes, ARIA roles)
- Use broad selectors for consistent styling
- Avoid emotion-cache classes that change
- Focus on semantic HTML elements
"""

SURVEY_STYLES = """
<style>
/* ========================================
   LAYOUT & SPACING
   ======================================== */

.block-container {
    padding-top: 3rem;
    padding-bottom: 3rem;
    padding-left: 5rem;
    padding-right: 5rem;
    max-width: 900px;
}

h1, h2, h3 {
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
}

p {
    margin-bottom: 1.5rem;
    line-height: 1.8;
    font-size: 18px;
}

hr {
    margin-top: 2.5rem;
    margin-bottom: 2.5rem;
}

/* ========================================
   BUTTONS
   ======================================== */

.stButton > button {
    font-size: 18px;
    padding: 8px 30px;
    margin-top: 1rem;
}

/* ========================================
   FORM ELEMENTS - Broad, Sustainable Styling
   ======================================== */

/* All form containers */
.stSelectbox, .stTextArea, .stRadio, .stSlider {
    margin-bottom: 0.25rem !important;
}

/* Labels: match body font and tighten spacing */
label, .stMarkdown label {
    font-size: 18px !important;
    font-weight: 500 !important;
    color: inherit !important;
    margin-bottom: 0rem !important;
}

/* ========================================
   SLIDER - Sustainable Styling
   ======================================== */

.stSlider {
    max-width: 80%;
    margin-left: 0.5rem;
    margin-top: 0rem !important;
    margin-bottom: 0rem !important;
}

[role="slider"] {
    width: 15px !important;
    height: 15px !important;
}

.stSlider [data-baseweb="slider"] { 
    margin-top: 0rem !important; 
    margin-bottom: 0rem !important; 
}

.stSlider [data-baseweb="slider"] div { 
    font-size: 14px; 
    color: inherit;
}

.stSlider span {
    color: gray !important;
}

.stElementContainer {
    margin-bottom: 0rem;
}

/* ========================================
   RADIO BUTTONS - Horizontal Layout
   ======================================== */

.stRadio > div {
    display: flex;
    flex-direction: row;
    gap: 1rem;
    flex-wrap: wrap;
}

.stRadio > div > label {
    margin-right: 1rem;
    margin-bottom: 0.5rem;
}

/* ========================================
   BUTTON STYLING
   ======================================== */

.stButton > button[kind="primary"],
button[kind="primary"] {
    background-color: #28a745 !important;
    border-color: #28a745 !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover,
button[kind="primary"]:hover {
    background-color: #218838 !important;
    border-color: #1e7e34 !important;
    color: white !important;
}

.stButton > button[kind="primary"]:active,
button[kind="primary"]:active {
    background-color: #1e7e34 !important;
    border-color: #1c7430 !important;
}

.stButton > button[kind="primary"]:focus:not(:active),
button[kind="primary"]:focus:not(:active) {
    background-color: #28a745 !important;
    border-color: #28a745 !important;
    box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.5) !important;
}

/* ========================================
   INFO BOXES
   ======================================== */

.stInfo {
    border-left: 4px solid #17a2b8;
    background-color: #d1ecf1;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 4px;
}

.stSuccess {
    border-left: 4px solid #28a745;
    background-color: #d4edda;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 4px;
}

</style>
"""


def get_question_style():
    """
    Returns inline style dict for questions.
    More sustainable than CSS for frequently changing elements.
    """
    return {
        'font-size': '20px',
        'font-weight': '600',
        'color': '#2c3e50',
        'margin-bottom': '1rem'
    }


def get_slider_container_style():
    """
    Returns inline style for slider containers.
    """
    return {
        'margin-bottom': '1.5rem'
    }
