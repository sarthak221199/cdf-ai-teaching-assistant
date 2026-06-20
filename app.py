import json
import re
from html import escape
from typing import List, Optional

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

    .board h2, .board h3, .board p, .board li {
        color: white;
    }

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

    .small-muted {
        color: #64748b;
        font-size: 0.9rem;
    }

    .tts-box button {
        background: #16a34a;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.65rem 1rem;
        font-weight: 700;
        cursor: pointer;
    }

    /* -----------------------------
       Improved Projected Visual
    ----------------------------- */
    .visual-board {
        background: linear-gradient(135deg, #e8f4ff 0%, #f7fbff 100%);
        border-radius: 28px;
        padding: 34px;
        margin-top: 18px;
        margin-bottom: 30px;
        border: 1px solid #d7ecff;
        box-shadow: 0 8px 24px rgba(30, 64, 175, 0.10);
    }

    .visual-main {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: white;
        padding: 22px 28px;
        border-radius: 22px;
        text-align: center;
        max-width: 620px;
        margin: 0 auto;
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.28);
    }

    .visual-main-title {
        font-size: 30px;
        font-weight: 800;
        line-height: 1.2;
    }

    .visual-main-subtitle {
        font-size: 16px;
        margin-top: 8px;
        opacity: 0.95;
    }

    .visual-arrow {
        text-align: center;
        font-size: 38px;
        font-weight: 900;
        color: #1e40af;
        margin: 14px 0;
    }

    .visual-card-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 18px;
    }

    .visual-card {
        background: white;
        border-radius: 22px;
        padding: 22px 16px;
        text-align: center;
        min-height: 145px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 12px;
    }

    .visual-icon {
        font-size: 38px;
    }

    .visual-text {
        font-size: 20px;
        font-weight: 750;
        color: #111827;
        line-height: 1.25;
    }

    @media (max-width: 900px) {
        .visual-card-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 600px) {
        .visual-card-grid {
            grid-template-columns: 1fr;
        }

        .visual-main-title {
            font-size: 24px;
        }
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


def render_projected_visual(title: str, visual_keywords: List[str]):
    """Render a clean smart-board friendly classroom visual."""
    icons = ["🌱", "⚡", "🧠", "🔍", "📘", "🧪", "🌍", "💡"]

    keywords = visual_keywords[:4] if visual_keywords else ["Idea", "Example", "Recall", "Practice"]

    while len(keywords) < 4:
        keywords.append("Point")

    safe_title = escape(str(title))

    cards_html = ""

    for i, keyword in enumerate(keywords):
        icon = icons[i % len(icons)]
        safe_keyword = escape(str(keyword))

        cards_html += (
            f'<div class="visual-card">'
            f'<div class="visual-icon">{icon}</div>'
            f'<div class="visual-text">{safe_keyword}</div>'
            f'</div>'
        )

    html = (
        f'<div class="visual-board">'
        f'<div class="visual-main">'
        f'<div class="visual-main-title">{safe_title}</div>'
        f'<div class="visual-main-subtitle">Classroom Smart Board Visual</div>'
        f'</div>'
        f'<div class="visual-arrow">↓</div>'
        f'<div class="visual-card-grid">'
        f'{cards_html}'
        f'</div>'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)

def build_concept_prompt(topic: str, grade: str, language: str) -> str:
    return f"""
You are a voice-enabled AI teaching assistant for a government school classroom.
Students understand Hindi + English mixed Hinglish. Be warm, simple, and teacher-friendly.

Task: Explain the concept for smart-board projection.

Topic/request: {topic}
Grade: {grade}
Output language style: {language}

Language rules:
- If language is "Simple English", write only in simple English.
- If language is "Hindi in Devanagari script", write Hindi using Devanagari script.
- If language is "Hinglish / Roman Hindi", write Hindi-English mix using English letters.
- Hinglish example: "Bacho, cloud computing ka matlab hai internet par data save karna."

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
  "story_explanation": "simple explanation under 90 words",
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

Language rules:
- If language is "Simple English", write only in simple English.
- If language is "Hindi in Devanagari script", write Hindi using Devanagari script.
- If language is "Hinglish / Roman Hindi", write Hindi-English mix using English letters.
- Hinglish example: "Bacho, chaliye ek quick quiz karte hain."

Strict rules:
- Questions must be simple and classroom-friendly.
- Include answer key and short explanation.
- Do not use harmful, political, or unrelated content.
- Keep each question concise.
- Return only valid JSON.
- No markdown.
- No extra text before or after JSON.
- Do not use line breaks inside string values.

Return JSON exactly in this format:
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

    grade = st.selectbox(
        "Class / Grade",
        ["Class 5", "Class 6", "Class 7", "Class 8", "Class 9", "Class 10"],
        index=1,
    )

    language = st.selectbox(
        "Language style",
        ["Hinglish / Roman Hindi", "Hindi in Devanagari script", "Simple English"],
        index=0,
    )

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

    input_type = st.radio(
        "Input method",
        ["Type topic/request", "Speak / upload audio"],
        horizontal=True,
    )

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

        uploaded_audio = st.file_uploader(
            "Or upload audio",
            type=["wav", "mp3", "m4a", "webm"],
        )

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
            st.markdown(
                f"<div class='step-card'><b>{i}.</b> {escape(str(p))}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Projected Visual")
        render_projected_visual(title, visual_keywords)

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

        speech_button(
            announcement + " " + " ".join([q.get("question", "") for q in questions])
        )

        st.markdown("### Quiz for smart-board")

        for idx, q in enumerate(questions, start=1):
            st.markdown(
                f"<div class='quiz-card'><h4>Q{idx}. {escape(str(q.get('question', '')))}</h4>",
                unsafe_allow_html=True,
            )

            for opt in q.get("options", []):
                st.write(opt)

            with st.expander("Show answer"):
                st.success(f"Answer: {q.get('answer', '')}")
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