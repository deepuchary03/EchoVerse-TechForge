import threading
from pydub import AudioSegment

def text_to_mp3_watson_fast(text, voice="en-US_AllisonV3Voice", filename=None, chunk_size=300):
    """
    Faster Watson TTS: Split text into chunks, synthesize in parallel, merge audio
    Args:
        text (str): Text to convert to speech
        voice (str): IBM Watson voice name
        filename (str): Output filename for the MP3 file
        chunk_size (int): Number of characters per chunk
    Returns:
        str: Path to the generated MP3 file
    """
    try:
        api_key = os.getenv("IBM_WATSON_TTS_APIKEY")
        url = os.getenv("IBM_WATSON_TTS_URL")
        if not api_key or not url:
            raise ValueError("IBM Watson TTS credentials not found in environment variables.")
        authenticator = IAMAuthenticator(api_key)
        tts = TextToSpeechV1(authenticator=authenticator)
        tts.set_service_url(url)
        cleaned_text = clean_text_for_tts(text)
        if not cleaned_text.strip():
            raise ValueError("No valid text provided for TTS conversion")
        # Split text into chunks
        sentences = cleaned_text.split('. ')
        chunks = []
        current = ''
        for s in sentences:
            if len(current) + len(s) + 2 > chunk_size:
                chunks.append(current.strip())
                current = s + '. '
            else:
                current += s + '. '
        if current.strip():
            chunks.append(current.strip())
        audio_segments = [None] * len(chunks)
        def synth_chunk(idx, chunk):
            response = tts.synthesize(chunk, voice=voice, accept='audio/mp3').get_result()
            audio_segments[idx] = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
        threads = []
        for i, chunk in enumerate(chunks):
            t = threading.Thread(target=synth_chunk, args=(i, chunk))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        # Filter out None segments
        valid_segments = [seg for seg in audio_segments if seg is not None]
        if not valid_segments:
            raise RuntimeError("All TTS chunks failed to synthesize. No audio output generated.")
        final_audio = valid_segments[0]
        for seg in valid_segments[1:]:
            final_audio += seg
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            filename = temp_file.name
            temp_file.close()
        final_audio.export(filename, format="mp3")
        return filename
    except Exception as e:
        st.error(f"IBM Watson TTS fast conversion failed: {str(e)}")
        raise e
import os
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

def text_to_mp3_watson(text, voice="en-US_AllisonV3Voice", filename=None):
    """
    Convert text to MP3 using IBM Watson Text-to-Speech with voice selection
    Args:
        text (str): Text to convert to speech
        voice (str): IBM Watson voice name
        filename (str): Output filename for the MP3 file
    Returns:
        str: Path to the generated MP3 file
    """
    try:
        api_key = os.getenv("IBM_WATSON_TTS_APIKEY")
        url = os.getenv("IBM_WATSON_TTS_URL")
        if not api_key or not url:
            raise ValueError("IBM Watson TTS credentials not found in environment variables.")
        authenticator = IAMAuthenticator(api_key)
        tts = TextToSpeechV1(authenticator=authenticator)
        tts.set_service_url(url)
        cleaned_text = clean_text_for_tts(text)
        if not cleaned_text.strip():
            raise ValueError("No valid text provided for TTS conversion")
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            filename = temp_file.name
            temp_file.close()
        response = tts.synthesize(
            cleaned_text,
            voice=voice,
            accept='audio/mp3'
        ).get_result()
        with open(filename, 'wb') as audio_file:
            audio_file.write(response.content)
        return filename
    except Exception as e:
        st.error(f"IBM Watson TTS conversion failed: {str(e)}")
        raise e
from gtts import gTTS
import io
import tempfile
import streamlit as st

def text_to_mp3_gtts(text, language="en", filename=None):
    """
    Convert text to MP3 using Google Text-to-Speech
    
    Args:
        text (str): Text to convert to speech
        language (str): Language code (en, hi, es, fr, etc.)
        filename (str): Output filename for the MP3 file
    
    Returns:
        str: Path to the generated MP3 file
    """
    try:
        # Clean and prepare text for TTS
        cleaned_text = clean_text_for_tts(text)
        
        if not cleaned_text.strip():
            raise ValueError("No valid text provided for TTS conversion")
        
        # Create gTTS object
        tts = gTTS(
            text=cleaned_text,
            lang=language,
            slow=False,
            lang_check=True
        )
        
        # If no filename provided, create a temporary file
        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            filename = temp_file.name
            temp_file.close()
        
        # Save to file
        tts.save(filename)
        
        return filename
    
    except Exception as e:
        st.error(f"TTS conversion failed: {str(e)}")
        raise e

def clean_text_for_tts(text):
    """
    Clean and prepare text for better TTS output
    
    Args:
        text (str): Raw text input
    
    Returns:
        str: Cleaned text suitable for TTS
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = " ".join(text.split())
    
    # Remove or replace problematic characters
    replacements = {
        """: '"',
        """: '"',
        "'": "'",
        "'": "'",
        "—": "-",
        "–": "-",
        "…": "...",
        "\n\n": ". ",
        "\n": " ",
        "\t": " "
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Ensure sentences end properly
    text = text.strip()
    if text and not text.endswith(('.', '!', '?')):
        text += '.'
    
    # Limit text length for TTS (gTTS has character limits)
    max_length = 4500  # Conservative limit for gTTS
    if len(text) > max_length:
        # Try to cut at sentence boundary
        sentences = text.split('. ')
        truncated = ""
        for sentence in sentences:
            if len(truncated + sentence + '. ') > max_length:
                break
            truncated += sentence + '. '
        text = truncated.strip()
        
        # If still too long, hard truncate
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
    
    return text

def get_supported_languages():
    """
    Return a dictionary of supported languages and their codes
    """
    return {
        "English": "en",
        "Hindi": "hi", 
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Russian": "ru",
        "Japanese": "ja",
        "Korean": "ko",
        "Chinese": "zh"
    }

def validate_language_code(lang_code):
    """
    Validate if the language code is supported by gTTS
    """
    supported_codes = list(get_supported_languages().values())
    return lang_code in supported_codes
