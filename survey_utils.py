"""
Utility functions for the reviewer survey application.
"""

import io
import wave
import streamlit as st
import openai


# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=st.secrets.get('OPENAI_KEY', ''))


HIDDEN_PAGES = {1, 2}


def _compute_target_page(current_page: int, direction: str) -> int:
    """Return the next visible page index for the requested direction."""
    step = 1 if direction == 'next' else -1
    target_page = current_page + step
    while target_page in HIDDEN_PAGES and target_page >= 0:
        target_page += step
    if target_page < 0:
        target_page = 0
    return target_page


def normalize_page(page_number: int) -> int:
    """Ensure the given page number is visible by skipping hidden pages."""
    if page_number in HIDDEN_PAGES:
        forward_page = _compute_target_page(page_number, 'next')
        if forward_page != page_number:
            return forward_page
        return _compute_target_page(page_number, 'back')
    return page_number


def _go_to_page(target_page: int):
    st.session_state['page'] = target_page
    st.rerun()


def next_page():
    """Navigate to the next visible page."""
    current_page = st.session_state.get('page', 0)
    target_page = _compute_target_page(current_page, 'next')
    _go_to_page(target_page)


def previous_page():
    """Navigate to the previous visible page."""
    current_page = st.session_state.get('page', 0)
    target_page = _compute_target_page(current_page, 'back')
    _go_to_page(target_page)


def save_and_navigate(direction: str, **responses):
    """
    Save responses to session state and navigate.
    
    Args:
        direction: 'next' or 'back'
        **responses: Key-value pairs to save to survey_responses
    """
    for key, value in responses.items():
        if value is not None:
            st.session_state['survey_responses'][key] = value
    
    participant_id = st.session_state['survey_responses'].get('participant_id')
    current_page = st.session_state.get('page', 0)
    target_page = _compute_target_page(current_page, direction)

    if participant_id:
        from survey_data import save_session_state
        save_session_state(participant_id, target_page, st.session_state['survey_responses'])

    _go_to_page(target_page)


def validate_required_fields(*fields):
    """
    Validate that all required fields are filled.
    
    Args:
        *fields: Field values to validate
        
    Returns:
        bool: True if all fields are valid, False otherwise
    """
    return all(field is not None and field != "" and field != "Not selected" for field in fields)


def display_pr_context(pr_url=None, issue_url=None):
    """
    Display PR context information if available.
    
    Args:
        pr_url: PR URL
        issue_url: Issue URL
    """
    if pr_url or issue_url:
        st.info(f"""
        **PR:** {pr_url or 'N/A'}
        """)
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)


def get_audio_duration(file):
    """Get the duration of an audio file in seconds."""
    try:
        with wave.open(file, 'rb') as audio:
            frames = audio.getnframes()
            rate = audio.getframerate()
            duration_seconds = frames / float(rate)
            return duration_seconds
    except wave.Error:
        st.error("Audio format not supported. Please upload a WAV file.")
        return None


def record_audio(question_key, min_duration=20, max_duration=600):
    """
    Record and transcribe audio for a question.
    
    Args:
        question_key: Unique key for the question
        min_duration: Minimum audio duration in seconds
        max_duration: Maximum audio duration in seconds
        
    Returns:
        The transcribed (and optionally edited) text, or None if not yet completed
    """
    work_audio = None
    
    # Prefer stable API if available
    if hasattr(st, "audio_input"):
        work_audio = st.audio_input(
            "Your voice recording will not be stored; only a transcript of the audio will be collected. ",
            key=f"audio_{question_key}"
        )
    elif hasattr(st, "experimental_audio_input"):
        work_audio = st.experimental_audio_input(
            "Your voice recording will not be stored; only a transcript of the audio will be collected. "
            f"Please provide at least {min_duration} seconds of audio and restrict your recording to "
            f"{max_duration // 60} minutes or less.",
            key=f"audio_{question_key}"
        )
    else:
        st.info("Audio recording is not supported in this Streamlit version.")

    if st.button("Transcribe", key=f"transcript_{question_key}"):
        if work_audio:
            # Read the audio bytes
            audio_bytes = work_audio.read()
            audio_file = io.BytesIO(audio_bytes)
            
            # Get the duration of the audio file
            duration_seconds = get_audio_duration(audio_file)
            
            if duration_seconds is None:
                st.error("Unsupported audio format. Please record in WAV format.")
            elif duration_seconds < min_duration:
                st.error(f"Please record at least {min_duration} seconds of audio before proceeding.")
            elif duration_seconds > max_duration:
                st.error(f"Please record less than {max_duration // 60} minutes of audio.")
            else:
                st.info("Please wait while we transcribe your audio... Do not refresh the page or click the button again.")
                try:
                    audio_file.seek(0)
                    if not hasattr(audio_file, 'name'):
                        audio_file.name = 'audio.wav'
                    transcription = openai_client.audio.transcriptions.create(
                        model='whisper-1',
                        file=audio_file
                    )
                    st.session_state[f'audio_transcript_{question_key}'] = transcription.text
                    st.success("Transcription complete. Please review and edit if needed.")
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
        else:
            st.warning("Please record audio first before transcribing.")

    # Display the transcript for review and editing
    if f'audio_transcript_{question_key}' in st.session_state:
        edited_transcript = st.text_area(
            "Review and edit your transcript below before submitting:",
            value=st.session_state[f'audio_transcript_{question_key}'],
            key=f"edit_transcript_{question_key}"
        )
        return edited_transcript
    
    return None
