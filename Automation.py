import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
from dotenv import load_dotenv
import os, re, requests, json
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="WebinarPilot AI", page_icon="🎙️", layout="wide")

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_video_id(url):
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})", url)
    if not match:
        raise ValueError("Invalid YouTube URL")
    return match.group(1)

def get_video_info(video_id):
    try:
        resp = requests.get(
            f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
            timeout=5
        )
        data = resp.json()
        return {
            "title": data.get("title", "Unknown Title"),
            "author": data.get("author_name", "Unknown Channel"),
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        }
    except:
        return {"title": "Unknown Title", "author": "Unknown Channel",
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"}

def get_transcript(video_id):
    fetcher = YouTubeTranscriptApi()
    transcript = fetcher.fetch(video_id)
    return " ".join(s.text for s in transcript)

def run_agent(client, system_prompt, user_prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=1000,
    )
    return response.choices[0].message.content.strip()

# ── Agents ────────────────────────────────────────────────────────────────────
def summary_agent(client, transcript, content_type):
    return run_agent(client,
        system_prompt=f"""You are an executive briefing specialist for {content_type} content.
Distill content into sharp, executive-ready summaries. No fluff.""",
        user_prompt=f"""Read this {content_type} transcript and write:
1. A 150-word executive summary.
2. Exactly 5 key takeaways as bullet points — each one a single crisp sentence.

Transcript:
{transcript[:8000]}"""
    )

def learning_agent(client, transcript, content_type):
    return run_agent(client,
        system_prompt=f"""You are an operations and learning specialist for {content_type} content.
Extract specific, actionable items. Never write vague items like "learn more".""",
        user_prompt=f"""Read this {content_type} transcript and extract:
1. 4-6 specific action items as checkboxes: - [ ] Action
2. A FAQ section with 4 Q&A pairs.
3. 10 SEO keywords (one per line).

Transcript:
{transcript[:8000]}"""
    )

def marketing_agent(client, transcript, content_type):
    return run_agent(client,
        system_prompt=f"""You are a senior B2B marketing copywriter specialising in LinkedIn content about {content_type}s.
Write posts that feel like a real person sharing genuine insights — not corporate announcements.""",
        user_prompt=f"""Write a LinkedIn post based on this {content_type}.
- Strong hook (not "I attended a {content_type} today")
- 2-3 specific insights
- End with an engaging question
- 200-250 words, 3-4 hashtags

Also write 5 social captions (under 280 chars each).

Transcript:
{transcript[:8000]}"""
    )

def newsletter_agent(client, transcript, content_type):
    return run_agent(client,
        system_prompt=f"""You are an email marketing specialist writing about {content_type} content.
Write newsletters people actually read. Be warm, specific, never generic.""",
        user_prompt=f"""Based on this {content_type} transcript write:

1. NEWSLETTER (300 words): subject line, hook, 2-3 insights, CTA
2. FOLLOW-UP EMAIL (150 words): subject, recap, [RECORDING_LINK], CTA, sign-off

Transcript:
{transcript[:8000]}"""
    )

def send_to_make(webhook_url, content, video_info, content_type):
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "content_type": content_type,
        "video_title": video_info["title"],
        "video_author": video_info["author"],
        "doc_title": f"{content_type} Notes — {video_info['title']} ({datetime.utcnow().strftime('%b %d, %Y')})",
        "summary": content.get("summary", ""),
        "actions_faq_seo": content.get("learning", ""),
        "linkedin_social": content.get("marketing", ""),
        "newsletter_email": content.get("newsletter", ""),
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=15)
        resp.raise_for_status()
        return True, "✅ Sent to Make.com!"
    except Exception as e:
        return False, f"⚠️ Make.com error: {e}"

# ── Workflow sidebar ──────────────────────────────────────────────────────────
def render_workflow(steps):
    """
    steps = list of (label, status) where status is 'done', 'active', or 'pending'
    """
    icons = {"done": "✅", "active": "⏳", "pending": "⬜"}
    lines = []
    for i, (label, status) in enumerate(steps):
        lines.append(f"{icons[status]} {label}")
        if i < len(steps) - 1:
            lines.append("↓")
    st.sidebar.markdown("\n\n".join(lines))

# ── Layout ────────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Settings")

content_type = st.sidebar.radio(
    "Content Type",
    ["Webinar", "Podcast", "Course", "Meeting Recording"],
    index=0
)

st.sidebar.divider()
st.sidebar.subheader("🔄 Workflow")
workflow_placeholder = st.sidebar.empty()

# Initial workflow state
def show_workflow(transcript=False, ai=False, content=False, docs=False, gmail=False, slack=False):
    steps = [
        ("Transcript",          "done" if transcript else "pending"),
        ("AI Analysis",         "done" if ai else ("active" if transcript else "pending")),
        ("Content Generation",  "done" if content else ("active" if ai else "pending")),
        ("Google Docs",         "done" if docs else ("active" if content else "pending")),
        ("Gmail",               "done" if gmail else ("active" if docs else "pending")),
        ("Slack",               "done" if slack else ("active" if gmail else "pending")),
    ]
    with workflow_placeholder.container():
        render_workflow(steps)

show_workflow()

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🎙️ WebinarPilot AI")
st.caption(f"Selected: **{content_type}** · Paste a YouTube URL → get content assets")

url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("🚀 Generate", type="primary"):
    if not url:
        st.warning("Enter a URL first.")
        st.stop()

    try:
        video_id = get_video_id(url)
    except:
        st.error("Invalid YouTube URL.")
        st.stop()

    # Video info
    info = get_video_info(video_id)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(info["thumbnail"], use_container_width=True)
    with col2:
        st.markdown(f"### {info['title']}")
        st.caption(f"📺 {info['author']} · {content_type}")
    st.divider()

    progress = st.progress(0)
    status = st.empty()

    # Step 1: Transcript
    status.markdown("**Step 1/5 — Extracting transcript...**")
    progress.progress(5)
    try:
        transcript = get_transcript(video_id)
    except Exception as e:
        st.error(f"Transcript error: {e}")
        st.stop()
    progress.progress(20)
    show_workflow(transcript=True)

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    results = {}

    # Step 2
    status.markdown("**Step 2/5 — 🧠 Summary Agent...**")
    results["summary"] = summary_agent(client, transcript, content_type)
    progress.progress(40)
    show_workflow(transcript=True, ai=True)

    # Step 3
    status.markdown("**Step 3/5 — 📚 Learning Agent...**")
    results["learning"] = learning_agent(client, transcript, content_type)
    progress.progress(55)

    # Step 4
    status.markdown("**Step 4/5 — 📣 Marketing Agent...**")
    results["marketing"] = marketing_agent(client, transcript, content_type)
    progress.progress(70)

    # Step 5
    status.markdown("**Step 5/5 — ✉️ Newsletter Agent...**")
    results["newsletter"] = newsletter_agent(client, transcript, content_type)
    progress.progress(90)
    show_workflow(transcript=True, ai=True, content=True)

    # Make.com
    webhook_url = os.getenv("MAKE_WEBHOOK_URL", "")
    docs_ok = gmail_ok = slack_ok = False
    if webhook_url:
        status.markdown("**Sending to Make.com → Google Docs, Gmail, Slack...**")
        ok, msg = send_to_make(webhook_url, results, info, content_type)
        if ok:
            docs_ok = gmail_ok = slack_ok = True
        st.info(msg)

    progress.progress(100)
    status.empty()
    show_workflow(transcript=True, ai=True, content=True,
                  docs=docs_ok, gmail=gmail_ok, slack=slack_ok)

    st.success("✅ Done! All agents completed.")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧠 Summary & Takeaways",
        "📚 Actions, FAQ & SEO",
        "📣 LinkedIn & Social",
        "✉️ Newsletter & Email",
    ])
    def render_section(content, filename, key):
        # Rendered, formatted view — wrap in a styled container, but let
        # Streamlit's own markdown engine parse **bold** and * bullets
        with st.container(border=True):
            st.markdown(content)
        st.write("")
        # Raw/copyable view tucked away so it doesn't clutter the main display
        with st.expander("📋 Copy raw text"):
            st.text_area("", content, height=200, key=f"raw_{key}", label_visibility="collapsed")
        st.download_button("⬇️ Download", content, filename, key=f"dl_{key}")

    with tab1:
        render_section(results["summary"], "summary.txt", "t1")
    with tab2:
        render_section(results["learning"], "actions.txt", "t2")
    with tab3:
        render_section(results["marketing"], "linkedin.txt", "t3")
    with tab4:
        render_section(results["newsletter"], "newsletter.txt", "t4")
