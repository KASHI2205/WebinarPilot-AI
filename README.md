# 🎙️ WebinarPilot AI

Turn any webinar, podcast, course, or meeting recording into a full suite of 
ready-to-publish content — automatically.

Paste a YouTube URL, and a pipeline of AI agents extracts the transcript and 
generates an executive summary, action items, SEO keywords, LinkedIn posts, 
and email newsletters — all in one click. Optionally, results are pushed 
straight to Google Docs, Gmail, and Slack via Make.com.

## ✨ Features

- **Multi-format support** — Webinars, podcasts, courses, or meeting recordings
- **Automatic transcript extraction** from any YouTube video
- **4 specialized AI agents** (powered by Groq / Llama 3.3 70B):
  - 🧠 **Summary Agent** — executive summary + key takeaways
  - 📚 **Learning Agent** — action items, FAQ, SEO keywords
  - 📣 **Marketing Agent** — LinkedIn post + social captions
  - ✉️ **Newsletter Agent** — newsletter + follow-up email
- **Live workflow tracker** showing each pipeline stage in real time
- **One-click Make.com integration** to auto-publish to Google Docs, Gmail & Slack
- **Export options** — copy raw text or download each asset directly

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **LLM:** Groq API (Llama 3.3 70B Versatile)
- **Transcript extraction:** youtube-transcript-api
- **Automation:** Make.com (webhook-based)

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A [Groq API key](https://console.groq.com)
- (Optional) A Make.com webhook URL for auto-publishing

### Installation

```bash
git clone https://github.com/<your-username>/webinarpilot-ai.git
cd webinarpilot-ai
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
MAKE_WEBHOOK_URL=your_make_webhook_url_here   # optional
```

### Run

```bash
streamlit run WEB.py
```

## 📋 How It Works

1. Paste a YouTube URL and select a content type
2. The app extracts the video transcript automatically
3. Four AI agents run in sequence, each generating a specific content asset
4. Results appear in organized tabs — view, copy, or download each one
5. If a Make.com webhook is configured, all content is automatically sent 
   to Google Docs, Gmail, and Slack

## 📸 Preview

*(Add a screenshot or GIF of the app here)*

## 🗺️ Roadmap

- [ ] Support for non-YouTube sources (Zoom, direct file upload)
- [ ] Custom agent/prompt configuration
- [ ] Multi-language transcript support
- [ ] Notion/Airtable integration

## 📄 License

MIT
