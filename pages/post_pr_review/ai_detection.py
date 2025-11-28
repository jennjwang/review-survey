"""
AI detection questions page for the reviewer survey.
"""

import streamlit as st
from survey_components import page_header, slider_question, navigation_buttons
from survey_utils import save_and_navigate, display_pr_context, record_audio
from survey_questions import AI_DETECTION_QUESTIONS
from survey_data import save_post_pr_review_responses, get_repository_assignment, get_assigned_pr_for_reviewer

# AI detection slider options (1-5 with labels)
AI_DETECTION_OPTIONS = [
    "Not selected",
    "1 - Very unlikely",
    "2 - Unlikely",
    "3 - Unsure / Neutral",
    "4 - Likely",
    "5 - Very likely"
]


def ai_detection_page():
    """Display the AI detection questions page."""
    # Check if already completed - skip to next page
    participant_id = st.session_state['survey_responses'].get('participant_id')
    pr_url = st.session_state['survey_responses'].get('pr_url')

    if participant_id and pr_url:
        from survey_data import check_ai_detection_completed
        if check_ai_detection_completed(participant_id, pr_url):
            print(f"[AI DETECTION] Already completed for {pr_url}, skipping to next page")
            st.session_state['page'] = st.session_state.get('page', 7) + 1
            st.rerun()
            return

    page_header(
        "AI-Generated Code Detection"
    )

    # Load PR context if missing
    assigned_repo = st.session_state['survey_responses'].get('assigned_repository')
    
    # Load repository if missing
    if participant_id and not assigned_repo:
        repo_result = get_repository_assignment(participant_id)
        if repo_result['success']:
            assigned_repo = repo_result['repository']
            st.session_state['survey_responses']['assigned_repository'] = assigned_repo
    
    # Load PR if missing
    if participant_id and assigned_repo and not pr_url:
        fetched = get_assigned_pr_for_reviewer(participant_id, assigned_repo)
        if fetched['success'] and fetched['pr']:
            pr = fetched['pr']
            st.session_state['survey_responses']['pr_url'] = pr['url']
            st.session_state['survey_responses']['issue_url'] = pr.get('issue_url')
            st.session_state['survey_responses']['issue_id'] = pr.get('issue_id')
            pr_url = pr['url']
    
    display_pr_context(pr_url=pr_url)

    # Load previous responses
    previous_ai_likelihood = st.session_state['survey_responses'].get('ai_likelihood')
    previous_ai_reasoning = st.session_state['survey_responses'].get('ai_reasoning', '')
    
    # AI likelihood question
    ai_likelihood = slider_question(
        AI_DETECTION_QUESTIONS['ai_likelihood'],
        AI_DETECTION_OPTIONS,
        "ai_likelihood",
        previous_ai_likelihood if previous_ai_likelihood else "Not selected",
        font_weight=600
    )
    
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    # AI reasoning question with audio or text option
    st.markdown(
        f"<p style='font-size:18px; font-weight:600; margin-bottom: 1.5rem;'>{AI_DETECTION_QUESTIONS['ai_reasoning']}</p>", 
        unsafe_allow_html=True
    )
    
    # Create tabs for audio and text input
    tab1, tab2 = st.tabs(["🎤 Record Audio", "⌨️ Type Response"])
    
    with tab1:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Click the microphone button below to record your response. Your audio will be transcribed automatically.
            </p>
            """, unsafe_allow_html=True)
        transcript = record_audio("ai_reasoning", min_duration=10, max_duration=180)
    
    with tab2:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Type your response in the text box below.
            </p>
            """, unsafe_allow_html=True)
        text_response = st.text_area(
            "Your response:",
            key="ai_reasoning_text",
            value=previous_ai_reasoning,
            height=150,
            placeholder="Type your answer here...",
            label_visibility="collapsed"
        )
    
    # Use whichever response is available
    if transcript:
        ai_reasoning = transcript
    elif text_response and text_response.strip():
        ai_reasoning = text_response
    else:
        ai_reasoning = previous_ai_reasoning
    
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    # AI review strategy question with audio or text option
    previous_ai_review_strategy = st.session_state['survey_responses'].get('ai_review_strategy', '')
    st.markdown(
        f"<p style='font-size:18px; font-weight:600; margin-bottom: 1.5rem;'>{AI_DETECTION_QUESTIONS['ai_review_strategy']}</p>", 
        unsafe_allow_html=True
    )
    
    # Create tabs for audio and text input
    tab3, tab4 = st.tabs(["🎤 Record Audio", "⌨️ Type Response"])
    
    with tab3:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Click the microphone button below to record your response. Your audio will be transcribed automatically.
            </p>
            """, unsafe_allow_html=True)
        strategy_transcript = record_audio("ai_review_strategy", min_duration=10, max_duration=180)
    
    with tab4:
        st.markdown("""
            <p style='font-size:14px; margin-bottom: 0.5rem; color: #666;'>
            Type your response in the text box below.
            </p>
            """, unsafe_allow_html=True)
        strategy_text_response = st.text_area(
            "Your response:",
            key="ai_review_strategy_text",
            value=previous_ai_review_strategy,
            height=150,
            placeholder="Type your answer here...",
            label_visibility="collapsed"
        )
    
    # Use whichever response is available
    if strategy_transcript:
        ai_review_strategy = strategy_transcript
    elif strategy_text_response and strategy_text_response.strip():
        ai_review_strategy = strategy_text_response
    else:
        ai_review_strategy = previous_ai_review_strategy
    
    # Validation function
    def validate():
        return ai_likelihood != "Not selected" and ai_reasoning.strip() != "" and ai_review_strategy.strip() != ""
    
    # Handlers with DB save on next (end of Post-PR-Review section)
    def handle_back():
        save_and_navigate('back', ai_likelihood=ai_likelihood, ai_reasoning=ai_reasoning, ai_review_strategy=ai_review_strategy)

    def handle_next():
        if not validate():
            return
        # Save current answers to session
        st.session_state['survey_responses']['ai_likelihood'] = ai_likelihood
        st.session_state['survey_responses']['ai_reasoning'] = ai_reasoning
        st.session_state['survey_responses']['ai_review_strategy'] = ai_review_strategy

        participant_id = st.session_state['survey_responses'].get('participant_id')
        pr_url = st.session_state['survey_responses'].get('pr_url', 'N/A')

        if participant_id:
            with st.spinner('Saving your responses...'):
                result = save_post_pr_review_responses(
                    participant_id,
                    pr_url,
                    st.session_state['survey_responses']
                )
            if not result.get('success'):
                st.error(f"⚠️ Error saving responses: {result.get('error')}")
                return

        save_and_navigate('next')

    # Navigation
    # Replace Next with a Submit button
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        back_clicked = st.button("Back", key="ai_detection_back")
    with col3:
        submit_clicked = st.button("Submit", key="ai_detection_submit")

    if back_clicked:
        handle_back()
    elif submit_clicked:
        if validate():
            handle_next()
        else:
            st.error("Please answer all questions before proceeding.")
