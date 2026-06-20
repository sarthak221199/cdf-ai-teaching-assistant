# Haryana Classroom AI Teaching Assistant

A voice-enabled AI teaching assistant prototype for smart-board classrooms where teachers and students speak Hindi + English mixed Hinglish.

This project is built for the Connecting Dreams Foundation Round 2 Technical Assignment.

## Chosen Option

**Option A — Voice-Enabled AI Teaching Assistant**

## Chosen Features

1. **Live Concept Simplification**  
   Teacher can type or speak a topic, and the app generates a simple Hinglish explanation with visual board content.

2. **Voice-Triggered Quizzing**  
   Teacher can ask for a quiz, and the app creates verbal quiz announcements with smart-board display and answer key.

## Tech Stack

- **Frontend + Backend:** Streamlit
- **AI Model:** Gemini API
- **Speech-to-Text:** Gemini audio transcription
- **Text-to-Speech:** Browser SpeechSynthesis API
- **Deployment:** Streamlit Community Cloud

## Prompt Design

The prompts are designed to:

- Use simple Hinglish / Hindi / English based on teacher selection.
- Keep language suitable for government school classrooms.
- Return structured JSON so the output can be shown cleanly on a smart board.
- Avoid unnecessary jargon.
- Provide teacher-ready scripts, examples, visuals, and quick checks.

## Localization

The prototype is optimized for Haryana classroom context:

- Hinglish explanation style.
- Simple teacher-friendly wording.
- Smart-board style large display.
- Real-life examples that can be understood by school students.

## How to Run Locally

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd cdf-ai-teaching-assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add Gemini API Key

Create a folder named `.streamlit` and a file named `secrets.toml` inside it:

```bash
mkdir .streamlit
```

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

### 4. Run the app

```bash
streamlit run app.py
```

## Deployment on Streamlit Community Cloud

1. Push this project to a public GitHub repository.
2. Open Streamlit Community Cloud.
3. Create a new app from your GitHub repo.
4. Add this secret in app settings:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

5. Deploy and copy the live URL.

## Demo Script for 3-Minute Video

1. Introduce the problem: A teacher in a Haryana government school needs hands-free AI support during live class.
2. Show the app interface.
3. Demonstrate Concept Simplification using a topic like "photosynthesis".
4. Show the smart-board explanation, visual, and read-aloud feature.
5. Demonstrate Voice-Triggered Quiz using the same topic.
6. Explain the tech stack and localization.
7. End with live URL and GitHub repo.

## Deliverables Checklist

- [ ] Live URL
- [ ] Public GitHub repo
- [ ] README
- [ ] 3-minute walkthrough video
