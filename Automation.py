import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from dotenv import load_dotenv
import os, re

load_dotenv()

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="WebinarPilot AI", page_icon="🎙️")
st.title("🎙️ WebinarPilot AI")
st.caption("Paste a YouTube webinar URL → get 9 content assets instantly.")

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})", url)
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)

def get_transcript(url):
    video_id = get_video_id(url)
    segments = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join(s["text"] for s in segments)

def analyze(transcript):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert post-webinar content assistant."},
            {"role": "user", "content": f"""
Analyze this webinar transcript and return exactly these 9 sections with these exact headers:

## EXECUTIVE SUMMARY
## KEY TAKEAWAYS
## ACTION ITEMS
## LINKEDIN POST
## NEWSLETTER DRAFT
## FOLLOW-UP EMAIL
## SOCIAL CAPTIONS
## FAQ
## SEO KEYWORDS

Transcript:
{transcript[:12000]}
"""}
        ],
        temperature=0.7,
        max_tokens=3500,
    )
    return response.choices[0].message.content

def parse(raw):
    headers = ["EXECUTIVE SUMMARY", "KEY TAKEAWAYS", "ACTION ITEMS",
               "LINKEDIN POST", "NEWSLETTER DRAFT", "FOLLOW-UP EMAIL",
               "SOCIAL CAPTIONS", "FAQ", "SEO KEYWORDS"]
    result = {}
    for i, h in enumerate(headers):
        next_h = headers[i + 1] if i + 1 < len(headers) else None
        pattern = rf"## {h}\n(.*?)" + (rf"(?=## {next_h})" if next_h else r"$")
        match = re.search(pattern, raw, re.DOTALL)
        result[h] = match.group(1).strip() if match else ""
    return result

# ── UI ────────────────────────────────────────────────────────────────────────
url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Generate", type="primary"):
    if not url:
        st.warning("Enter a URL first.")
        st.stop()

    with st.spinner("Extracting transcript..."):
        try:
            transcript = get_transcript(url)
        except Exception as e:
            st.error(f"Transcript error: {e}")
            st.stop()

    with st.spinner("Generating content with GPT-4o..."):
        try:
            raw = analyze(transcript)
            content = parse(raw)
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            st.stop()

    st.success("Done! 9 assets generated.")

    labels = {
        "EXECUTIVE SUMMARY": "📋 Summary",
        "KEY TAKEAWAYS": "💡 Takeaways",
        "ACTION ITEMS": "✅ Actions",
        "LINKEDIN POST": "💼 LinkedIn",
        "NEWSLETTER DRAFT": "📧 Newsletter",
        "FOLLOW-UP EMAIL": "✉️ Follow-up Email",
        "SOCIAL CAPTIONS": "📱 Social Captions",
        "FAQ": "❓ FAQ",
        "SEO KEYWORDS": "🔍 SEO Keywords",
    }

    tabs = st.tabs(list(labels.values()))
    for tab, (key, label) in zip(tabs, labels.items()):
        with tab:
            st.text_area("", content[key], height=300, key=key)
            st.download_button(
                "⬇️ Download",
                data=content[key],
                file_name=f"{key.lower().replace(' ', '_')}.txt",
                key=f"dl_{key}"
            )