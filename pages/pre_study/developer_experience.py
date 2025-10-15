"""
Developer experience page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, selectbox_question, text_area_question, navigation_buttons
from survey_utils import save_and_navigate
from survey_questions import EXPERIENCE_OPTIONS
from survey_data import save_pre_study_responses


def developer_experience_page():
    """Display the developer experience page."""
    page_header(
        "Developer Experience",
        "Tell us about your background and experience."
    )
    
    # Load previous responses
    previous_experience = st.session_state['survey_responses'].get('professional_experience', None)
    previous_occupation = st.session_state['survey_responses'].get('occupation_description', '')
    
    # Professional experience question
    professional_experience = selectbox_question(
        "How many years of professional development experience do you have?",
        EXPERIENCE_OPTIONS,
        "professional_experience",
        previous_experience
    )
    
    st.divider()
    
    # Occupation description question
    occupation_description = text_area_question(
        "Please briefly describe your current occupation.",
        "occupation_description",
        previous_occupation,
        height=100,
        placeholder="1-2 sentences to describe your work."
    )
    
    # Validation function
    def validate():
        return professional_experience and occupation_description.strip()
    
    # Custom navigation handlers with data saving
    def handle_back():
        save_and_navigate('back', 
                          professional_experience=professional_experience,
                          occupation_description=occupation_description)
    
    def handle_next():
        if not validate():
            return
        
        # Save to session state
        st.session_state['survey_responses']['professional_experience'] = professional_experience
        st.session_state['survey_responses']['occupation_description'] = occupation_description
        
        # Save to database
        participant_id = st.session_state['survey_responses'].get('participant_id')
        if participant_id:
            with st.spinner('Saving your responses...'):
                result = save_pre_study_responses(participant_id, st.session_state['survey_responses'])
            
            if result['success']:
                print(f"✅ Pre-study responses saved for participant {participant_id}")
                save_and_navigate('next',
                                professional_experience=professional_experience,
                                occupation_description=occupation_description)
            else:
                st.error(f"⚠️ Error saving responses: {result['error']}")
                print(f"Failed to save pre-study responses: {result['error']}")
        else:
            save_and_navigate('next',
                            professional_experience=professional_experience,
                            occupation_description=occupation_description)
    
    # Navigation
    navigation_buttons(
        on_back=handle_back,
        on_next=handle_next,
        back_key="dev_exp_back",
        next_key="dev_exp_next",
        validation_fn=validate,
        validation_error="Please fill out all fields before proceeding."
    )
