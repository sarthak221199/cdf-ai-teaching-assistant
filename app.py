import json
import re
from typing import Any, Dict, List, Optional

import streamlit as st
from google import genai
from google.genai import types

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Classroom AI Assistant",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #4b5563;
        margin-bottom: 1rem;
    }
    .board {
        background: #0f172a;
        color: white;
        padding: 1.2rem;
        border-radius: 18px;
        border: 6px solid #334155;
        box-shadow: 0 8px 30px rgba(15, 23, 42, 0.25);
    }
    .board h2, .board h3, .board p, .board li { color: white; }
    .big-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 1rem;
        border-radius: 16px;
        margin-bottom: 0.8rem;
    }
    .step-card {
        background: white;
        border-left: 6px solid #2563eb;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        color: #111827;
    }
    .quiz-card {
        background: white;
        border: 1px solid #cbd5e1;
        padding: 1rem;
        border-radius: 14px;
        margin-bottom: 1rem;
        color: #111827;
    }
    .small-muted { color: #64748b; font-size: 0.9rem; }
    .tts-box button {
        background: #16a34a;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1rem;
        font-weight: 700;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Helpers
# -----------------------------

def get_api_key() -> Optional[str]:
    """Read Gemini API key from Streamlit secrets."""
    try:
        return st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        return None


def get_client() -> genai.Client:
    api_key = get_api_key()
    if not api_key:
        st.error("Gemini API key missing. Add GEMINI_API_KEY in Streamlit secrets or .streamlit/secrets.toml.")
        st.stop()
    return genai.Client(api_key=api_key)

def clean_json(text: str) -> dict:
    import json
    import re

    if not text:
        raise ValueError("Empty response from model.")

    cleaned = text.strip()

    # Remove markdown code block if Gemini adds ```json
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    # Try direct JSON parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Try to extract JSON object from extra text
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    # Show model output for debugging
    raise ValueError(f"Could not parse JSON from model output. Raw output was:\n{cleaned}")


def call_gemini_text(prompt: str) -> str:
    client = get_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=5000,
            response_mime_type="application/json",
        ),
    )

    return response.text or ""


def transcribe_audio(audio_file, language_hint: str) -> str:
    client = get_client()
    audio_bytes = audio_file.read()
    mime_type = getattr(audio_file, "type", None) or "audio/wav"

    prompt = f"""
    Transcribe this teacher's audio accurately.
    The teacher may speak Hindi, English, or Hinglish.
    Language hint: {language_hint}.
    Return only the transcript text. Do not add explanation.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        ],
    )
    return (response.text or "").strip()


def speech_button(text: str, button_label: str = "🔊 Read aloud"):
    safe_text = json.dumps(text)
    html = f"""
    <div class="tts-box">
      <button onclick='speakText()'>{button_label}</button>
    </div>
    <script>
      function speakText() {{
        const text = {safe_text};
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'hi-IN';
        msg.rate = 0.92;
        msg.pitch = 1.0;
        window.speechSynthesis.speak(msg);
      }}
    </script>
    """
    st.components.v1.html(html, height=70)


def make_visual_svg(topic: str, keywords: List[str]) -> str:
    # Simple smart-board visual. It works offline and avoids image API dependency.
    clean_topic = topic[:42]
    words = keywords[:4] if keywords else ["Idea", "Example", "Recall", "Practice"]
    while len(words) < 4:
        words.append("Point")

    return f"""
    <svg width="100%" height="250" viewBox="0 0 900 250" xmlns="http://www.w3.org/2000/svg">
      <rect x="0" y="0" width="900" height="250" rx="22" fill="#e0f2fe"/>
      <rect x="350" y="85" width="200" height="80" rx="18" fill="#2563eb"/>
      <text x="450" y="118" text-anchor="middle" font-size="24" fill="white" font-weight="700">{clean_topic}</text>
      <text x="450" y="148" text-anchor="middle" font-size="16" fill="white">Classroom Visual</text>

      <circle cx="150" cy="55" r="42" fill="#22c55e"/>
      <text x="150" y="61" text-anchor="middle" font-size="15" fill="white" font-weight="700">{words[0][:14]}</text>
      <line x1="190" y1="70" x2="350" y2="105" stroke="#334155" stroke-width="3"/>

      <circle cx="740" cy="55" r="42" fill="#f97316"/>
      <text x="740" y="61" text-anchor="middle" font-size="15" fill="white" font-weight="700">{words[1][:14]}</text>
      <line x1="700" y1="70" x2="550" y2="105" stroke="#334155" stroke-width="3"/>

      <circle cx="160" cy="195" r="42" fill="#a855f7"/>
      <text x="160" y="201" text-anchor="middle" font-size="15" fill="white" font-weight="700">{words[2][:14]}</text>
      <line x1="200" y1="180" x2="350" y2="145" stroke="#334155" stroke-width="3"/>

      <circle cx="730" cy="195" r="42" fill="#ef4444"/>
      <text x="730" y="201" text-anchor="middle" font-size="15" fill="white" font-weight="700">{words[3][:14]}</text>
      <line x1="690" y1="180" x2="550" y2="145" stroke="#334155" stroke-width="3"/>
    </svg>
    """

def build_concept_prompt(topic: str, grade: str, language: str) -> str:
    return f"""
You are a voice-enabled AI teaching assistant for a government school classroom.
Students understand Hindi + English mixed Hinglish. Be warm, simple, and teacher-friendly.

Task: Explain the concept for smart-board projection.

Topic/request: {topic}
Grade: {grade}
Output language style: {language}

Strict rules:
- Use simple classroom language.
- Avoid difficult jargon.
- Make it useful for live teaching.
- Do not mention that you are an AI model.
- Keep every field concise.
- story_explanation must be maximum 90 words.
- teacher_script must be maximum 70 words.
- real_life_example must be maximum 35 words.
- Return only valid JSON.
- No markdown.
- No extra text before or after JSON.
- Do not use line breaks inside string values.

Return JSON exactly in this format:
{{
  "title": "short title",
  "one_line": "one sentence explanation",
  "story_explanation": "simple Hinglish explanation under 90 words",
  "key_points": ["point 1", "point 2", "point 3", "point 4"],
  "visual_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
  "teacher_script": "what teacher can say aloud under 70 words",
  "real_life_example": "one local/simple example under 35 words",
  "quick_check_question": "one oral question for students"
}}
"""


def build_quiz_prompt(topic: str, grade: str, language: str, count: int) -> str:
    return f"""
    You are a voice-enabled quiz assistant for a government school classroom.
    Students understand Hindi + English mixed Hinglish.

    Topic/request: {topic}
    Grade: {grade}
    Output language style: {language}
    Number of questions: {count}

    Strict rules:
    - Questions must be simple and classroom-friendly.
    - Include answer key and short explanation.
    - Do not use harmful, political, or unrelated content.
    - Return only valid JSON. No markdown.

    JSON format:
    {{
      "title": "quiz title",
      "announcement": "short verbal announcement for teacher",
      "questions": [
        {{
          "question": "question text",
          "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
          "answer": "A/B/C/D",
          "explanation": "one simple explanation"
        }}
      ]
    }}
    """


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.header("⚙️ Classroom Settings")
    mode = st.radio(
        "Choose feature",
        ["Live Concept Simplification", "Voice-Triggered Quizzing"],
        index=0,
    )
    grade = st.selectbox("Class / Grade", ["Class 5", "Class 6", "Class 7", "Class 8", "Class 9", "Class 10"], index=1)
    language = st.selectbox("Language style", ["Hinglish", "Simple Hindi", "Simple English"], index=0)
    quiz_count = st.slider("Quiz questions", 3, 8, 5)

    st.markdown("---")
    st.caption("Prototype for CDF Round 2 Technical Assignment")
    st.caption("Features: Concept Simplification + Voice Quiz")


# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="main-title">🎙️ Classroom AI Teaching Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Hands-free teaching support for smart-board classrooms in Hindi + English mixed Hinglish.</div>',
    unsafe_allow_html=True,
)

col_left, col_right = st.columns([1.1, 0.9], gap="large")

with col_left:
    st.markdown("### 1) Teacher input")
    input_type = st.radio("Input method", ["Type topic/request", "Speak / upload audio"], horizontal=True)

    transcript = ""
    if input_type == "Type topic/request":
        transcript = st.text_area(
            "Enter teacher command",
            placeholder="Example: Explain photosynthesis in simple Hinglish for Class 6",
            height=120,
        )
    else:
        st.info("Record audio using the microphone widget. If your browser does not support it, upload a WAV/MP3 file.")
        audio_file = None
        if hasattr(st, "audio_input"):
            audio_file = st.audio_input("Record teacher voice")
        uploaded_audio = st.file_uploader("Or upload audio", type=["wav", "mp3", "m4a", "webm"])
        final_audio = audio_file or uploaded_audio

        if final_audio and st.button("Transcribe audio"):
            with st.spinner("Listening and transcribing..."):
                transcript = transcribe_audio(final_audio, language)
                st.session_state["last_transcript"] = transcript

        transcript = st.session_state.get("last_transcript", "")
        if transcript:
            st.success("Transcript captured")
            st.write(transcript)

    generate = st.button("🚀 Generate classroom support", use_container_width=True)

with col_right:
    st.markdown("### 2) Smart-board preview")
    st.markdown(
        """
        <div class="big-card">
        <b>Demo idea:</b><br>
        Speak or type a teacher command. The app creates a board-ready explanation or quiz, and can read it aloud.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="big-card">
        <b>Example commands:</b><br>
        • Explain photosynthesis in Hinglish<br>
        • Make 5 quiz questions on water cycle<br>
        • Explain fractions using roti example<br>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# Generate output
# -----------------------------
if generate:
    if not transcript.strip():
        st.warning("Please type a topic/request or transcribe audio first.")
        st.stop()

    with st.spinner("Creating smart-board content..."):
        try:
            if mode == "Live Concept Simplification":
                raw = call_gemini_text(build_concept_prompt(transcript, grade, language))
                data = clean_json(raw)
                st.session_state["mode"] = mode
                st.session_state["output"] = data
                st.session_state["topic"] = transcript
            else:
                raw = call_gemini_text(build_quiz_prompt(transcript, grade, language, quiz_count))
                data = clean_json(raw)
                st.session_state["mode"] = mode
                st.session_state["output"] = data
                st.session_state["topic"] = transcript
        except Exception as e:
            st.error("Something went wrong while generating output.")
            st.exception(e)


# -----------------------------
# Render output
# -----------------------------
if "output" in st.session_state:
    data = st.session_state["output"]
    active_mode = st.session_state.get("mode", mode)
    topic = st.session_state.get("topic", "Topic")

    st.markdown("---")

    if active_mode == "Live Concept Simplification":
        title = data.get("title", "Concept Explanation")
        one_line = data.get("one_line", "")
        story = data.get("story_explanation", "")
        points = data.get("key_points", [])
        visual_keywords = data.get("visual_keywords", [])
        teacher_script = data.get("teacher_script", "")
        example = data.get("real_life_example", "")
        quick_q = data.get("quick_check_question", "")

        board_text = f"{title}. {one_line}. {story}. Key points: " + ", ".join(points)

        st.markdown('<div class="board">', unsafe_allow_html=True)
        st.subheader(f"📚 {title}")
        st.markdown(f"### {one_line}")
        st.write(story)
        st.markdown("#### Key Points")
        for i, p in enumerate(points, start=1):
            st.markdown(f"<div class='step-card'><b>{i}.</b> {p}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Projected Visual")
        st.components.v1.html(make_visual_svg(title, visual_keywords), height=270)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Teacher 30-sec script")
            st.info(teacher_script)
            speech_button(teacher_script or board_text)
        with c2:
            st.markdown("### Real-life example + quick check")
            st.success(example)
            st.warning(quick_q)

    else:
        title = data.get("title", "Classroom Quiz")
        announcement = data.get("announcement", "Let's start a quick quiz.")
        questions = data.get("questions", [])

        st.markdown('<div class="board">', unsafe_allow_html=True)
        st.subheader(f"🧠 {title}")
        st.markdown(f"### {announcement}")
        st.markdown("</div>", unsafe_allow_html=True)

        speech_button(announcement + " " + " ".join([q.get("question", "") for q in questions]))

        st.markdown("### Quiz for smart-board")
        for idx, q in enumerate(questions, start=1):
            st.markdown(f"<div class='quiz-card'><h4>Q{idx}. {q.get('question','')}</h4>", unsafe_allow_html=True)
            for opt in q.get("options", []):
                st.write(opt)
            with st.expander("Show answer"):
                st.success(f"Answer: {q.get('answer','')}")
                st.write(q.get("explanation", ""))
            st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Footer
# -----------------------------
st.markdown("---")
st.markdown(
    "<span class='small-muted'>Built as a prototype: Streamlit + Gemini API + audio transcription + browser text-to-speech.</span>",
    unsafe_allow_html=True,
)
