import json
import os
import re
import xml.etree.ElementTree as ET

import requests
import resend
from dotenv import load_dotenv
from openai import OpenAI

from config import VENDOR_NAME, VENDOR_PRODUCT, load_companies
from email_template import build_digest_email

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
resend.api_key = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")
TO_EMAIL = os.environ.get("TO_EMAIL")


def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences that models often wrap around HTML output."""
    text = text.strip()
    match = re.match(r"^```(?:\w+)?\s*\n?(.*?)\n?```$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    text = re.sub(r"^```(?:\w+)?\s*\n?", "", text)
    return re.sub(r"\n?```\s*$", "", text).strip()


def fetch_news_rss(company: str) -> list[dict]:
    """Fetches recent news items from Google News RSS."""
    clean_query = company.replace(" ", "+")
    url = (
        f"https://news.google.com/rss/search?q={clean_query}+stock+when:24h"
        "&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        articles = []
        for item in root.findall(".//item")[:8]:
            articles.append({
                "title": item.find("title").text,
                "link": item.find("link").text,
            })
        return articles
    except Exception as e:
        print(f"Error fetching news for {company}: {e}")
        return []


NO_NEWS_RESPONSE = "<p>No market-moving news today.</p>"


def ai_filter_and_summarize(company: str, articles: list[dict]) -> dict[str, str] | None:
    """Filter articles and return news bullets plus analyst insight.

    Returns None when there is no market-moving news to include in the digest.
    """
    if not articles:
        return None

    client = OpenAI(api_key=OPENAI_API_KEY)
    articles_text = "\n".join(
        [f"- Title: {a['title']} | Link: {a['link']}" for a in articles]
    )

    prompt = f"""
    You are an expert enterprise SaaS sales strategist for {VENDOR_NAME}, which sells {VENDOR_PRODUCT}.
    You are supporting an account executive trying to close a Port deal with {company} in the next 2-3 months.
    Below is a raw list of news articles from the last 24 hours regarding {company}.
    Your job is to ignore general product reviews, lifestyle fluff, or spam, and extract only news that could affect enterprise buying decisions for developer platform, engineering productivity, or internal tooling (e.g., earnings, CTO/engineering leadership changes, mergers & acquisitions, regulatory or security incidents, digital transformation, AI adoption, cloud modernization, budget cuts, or major engineering initiatives).

    Return a JSON object with exactly these keys:
    - "news_html": raw HTML only (wrapped in a <ul> list). Do not use markdown or code fences. For each relevant article, provide a 1-sentence bullet that hyper-links the title using the provided Link and briefly notes why it may matter for selling Port.io. Use an empty string if none of the articles are relevant to a Port sales motion.
    - "insight_html": raw HTML only with 2-3 concise sentences written for a Port seller. Explain how this news affects the likelihood, timing, or urgency of closing a Port deal in the next couple months. Reference relevant buyer personas (e.g., VP Engineering, Head of Platform, DevEx, CTO, CIO) where appropriate. Call out buying signals, procurement risks, and recommended next steps for positioning Port's agentic SDLC platform. Use one or more <p> tags. Use an empty string if none of the articles are relevant to a Port sales motion.

    Articles:
    {articles_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        news_html = strip_markdown_fences(data.get("news_html", "")).strip()
        insight_html = strip_markdown_fences(data.get("insight_html", "")).strip()
        if not news_html or news_html == NO_NEWS_RESPONSE:
            return None
        return {"news_html": news_html, "insight_html": insight_html}
    except Exception as e:
        print(f"AI generation failed for {company}: {e}")
        return None


def send_html_email(html_content: str, news_count: int) -> None:
    """Sends the formatted HTML digest via Resend."""
    try:
        params = {
            "from": FROM_EMAIL,
            "to": TO_EMAIL,
            "subject": f"Daily Market News Digest — {news_count} companies",
            "html": html_content,
        }
        email = resend.Emails.send(params)
        print(f"Email sent successfully via Resend! ID: {email['id']}")
    except Exception as e:
        print(f"Failed to send email via Resend: {e}")


if __name__ == "__main__":
    companies = load_companies()
    print(f"Starting daily market news scrape for {len(companies)} companies...")

    sections = []
    for company in companies:
        print(f"Processing {company}...")
        raw_news = fetch_news_rss(company)
        result = ai_filter_and_summarize(company, raw_news)
        if result:
            sections.append({"company": company, **result})
        else:
            print(f"No market-moving news for {company}; skipping.")

    if not sections:
        print("No market-moving news today. Skipping email.")
    else:
        email_body = build_digest_email(sections, news_count=len(sections))
        send_html_email(email_body, news_count=len(sections))
