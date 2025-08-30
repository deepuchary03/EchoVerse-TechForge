import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from granite_utils import load_granite_model, process_text_with_granite
from tts_utils import text_to_mp3_gtts
from PyPDF2 import PdfReader
import tempfile
import os

st.set_page_config(page_title="EchoVerse", page_icon="📖", layout="centered")

# ---------- Custom CSS (Whiter Components + Glass Style) ----------
st.markdown("""
    <style>
/* Background */
.stApp {
    background: linear-gradient(rgba(15,15,40,0.85), rgba(15,15,40,0.85)),
                url("https://images.unsplash.com/photo-1507842217343-583bb7270b66") no-repeat center center fixed;
    background-size: cover;
}

/* Title */
.main-title {
    font-size: 3rem !important;
    font-weight: bold;
    color: #ffffff;
    text-shadow: 2px 4px 8px rgba(0,0,0,0.7);
    margin-bottom: 0.3em;
    text-align: center;
}

/* Subtitle */
.subtitle {
    color: #f1f1f1;
    font-size: 1.2rem;
    margin-bottom: 2em;
    text-align: center;
    opacity: 0.9;
}

/* Glass Block */
.block {
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 1.2rem;
    padding: 1.6rem 2rem;
    margin-bottom: 1.4em;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    backdrop-filter: blur(14px);
    color: #ffffff;
}

/* Inputs */
.stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"], .stFileUploader {
    background: rgba(255, 255, 255, 0.7) !important;  /* soft frosted */
    color: #111 !important;
    border-radius: 0.7em !important;
    border: 1px solid rgba(200,200,200,0.4) !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    padding: 0.6em;
    transition: all 0.25s ease-in-out;
}

/* Hover + Focus states (no harsh white) */
.stTextArea textarea:focus, .stTextInput input:focus, 
.stSelectbox div[data-baseweb="select"]:hover {
    background: rgba(245, 245, 245, 0.85) !important; /* soft light gray instead of white */
    box-shadow: 0 0 0 3px rgba(123,47,247,0.35);
    border: 1px solid rgba(123,47,247,0.6) !important;
    outline: none !important;
}
/* Labels */
.stSelectbox label, .stTextArea label, .stTextInput label {
    color: #ffffff !important;
    font-weight: 500;
}

/* Buttons */
.stButton>button {
    color: #fff;
    background: linear-gradient(90deg,#7b2ff7,#f107a3);
    border: none;
    border-radius: .7em;
    font-weight: 600;
    padding: 0.7em 2em;
    font-size: 1.2em;
    margin-top:0.7em;
    transition: all .25s ease;
    box-shadow: 0 4px 15px rgba(123,47,247,0.5);
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(241,7,163,0.7);
}

/* Audio Player */
.stAudio {
    background: rgba(255,255,255,0.25);
    border-radius: 0.7em;
    padding: 0.6em;
    box-shadow: 0 2px 10px rgba(255,255,255,0.3);
}

/* Divider */
hr {
    border-top: 2.5px solid rgba(255,255,255,0.25);
    border-radius: 2px;
    margin: 1.7em 0 2em 0;
}

/* Text inside blocks */
.block h4, .block p, .block span, .block label {
    color: #ffffff !important;
}
            .stTextArea textarea {
    background: rgba(255, 255, 255, 0.12) !important;  /* same as .block / uploader */
    color: #ffffff !important;
    border-radius: 0.7em !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.35);
    backdrop-filter: blur(10px);
    padding: 0.8em;
    font-size: 1rem;
    transition: all 0.25s ease-in-out;
}

/* Textarea focus */
.stTextArea textarea:focus {
    background: rgba(255, 255, 255, 0.18) !important;
    box-shadow: 0 0 0 3px rgba(123,47,247,0.35);
    border: 1px solid rgba(123,47,247,0.6) !important;
    outline: none !important;
}
</style>

""", unsafe_allow_html=True)

# ---------- UI ----------
st.markdown('<div class="main-title">📖 EchoVerse</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Transform your words into stunning, expressive audiobooks with AI & TTS magic.</div>', unsafe_allow_html=True)
st.markdown('<hr>', unsafe_allow_html=True)

st.markdown('<div class="block">', unsafe_allow_html=True)
st.write("#### Upload your content or enter text")
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed")
with col2:
    text_input = st.text_area("Paste or type your story", height=220, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="block">', unsafe_allow_html=True)
st.write("#### Personalize narration")
col_tone, col_voice = st.columns(2)
with col_tone:
    tone = st.selectbox(
        "Narrative Tone",
        ["Neutral", "Suspenseful", "Inspiring"],
        key="tone_select"
    )
with col_voice:
    voice_style = st.selectbox(
        "Voice Style",
        ["Lisa", "Michael", "Allison", "Kate"],
        key="voice_select"
    )
st.caption(f"Active Tone: {tone} | Active Voice: {voice_style}")
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Functionality (unchanged) ----------
text = ""
if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]
    if file_type == "pdf":
        try:
            pdf = PdfReader(uploaded_file)
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        except Exception as e:
            st.error(f"❌ Error reading PDF file: {str(e)}")
    elif file_type == "txt":
        try:
            text = uploaded_file.read().decode('utf-8')
        except Exception as e:
            st.error(f"❌ Error reading text file: {str(e)}")
elif text_input:
    text = text_input

if st.button("✨ Generate Audiobook"):
    if not text.strip():
        st.error("❌ Please provide some text or upload a file first.")
    else:
        try:
            with st.spinner("🔄 Processing your story with IBM Granite..."):
                granite_pipe = load_granite_model()
                processed_text = process_text_with_granite(
                    text,
                    tone=tone.lower(),
                    style=voice_style,
                    granite_pipe=granite_pipe
                )
            with st.spinner("🎵 Generating your audiobook..."):
                st.markdown('<div class="block">', unsafe_allow_html=True)
                st.write("#### Original vs Generated Text")
                col_orig, col_gen = st.columns(2)
                with col_orig:
                    st.markdown("**Original Text**")
                    st.write(text)
                with col_gen:
                    st.markdown("**Generated Text**")
                    st.write(processed_text)
                st.markdown('</div>', unsafe_allow_html=True)

                watson_voice_map = {
                    "Lisa": "en-US_LisaV3Voice",
                    "Michael": "en-US_MichaelV3Voice",
                    "Allison": "en-US_AllisonV3Voice",
                    "Kate": "en-GB_KateV3Voice"
                }
                watson_voice = watson_voice_map.get(voice_style, "en-US_AllisonV3Voice")
                from tts_utils import text_to_mp3_watson
                tmp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                text_to_mp3_watson(processed_text, voice=watson_voice, filename=tmp_mp3.name)
                with open(tmp_mp3.name, "rb") as f:
                    audio_bytes = f.read()
                st.success("✅ Audiobook ready! Listen or download below.")
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    label="⬇️ Download Audiobook (MP3)",
                    data=audio_bytes,
                    file_name="EchoVerse_Audiobook.mp3",
                    mime="audio/mp3"
                )
                try:
                    os.unlink(tmp_mp3.name)
                except Exception:
                    pass
        except Exception as e:
            st.error("Please check your internet connection and try again.")
else:
    st.caption("⚡ Tip: Try different tones and voice styles for more expressive results!")
