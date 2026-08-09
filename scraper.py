import os
import re
import xml.etree.ElementTree as ET

import requests
import resend
from dotenv import load_dotenv
from openai import OpenAI

from config import load_companies
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


def ai_filter_and_summarize(company: str, articles: list[dict]) -> str:
    """Uses OpenAI to filter out fluff and write a brief financial summary."""
    if not articles:
        return "<p>No news found in the last 24 hours.</p>"

    client = OpenAI(api_key=OPENAI_API_KEY)
    articles_text = "\n".join(
        [f"- Title: {a['title']} | Link: {a['link']}" for a in articles]
    )

    prompt = f"""
    You are an expert financial analyst. Below is a raw list of news articles from the last 24 hours regarding {company}.
    Your job is to ignore general product reviews, lifestyle fluff, or spam, and extract only critical, market-moving news (e.g., earnings, executive changes, mergers & acquisitions, regulatory issues, major macroeconomic shifts).

    Format your response as raw HTML only (wrapped in a <ul> list). Do not use markdown or code fences. Provide a 1-sentence bullet point summary for each relevant piece of news, and hyper-link the title using the provided Link.
    If none of the articles are financially relevant, return exactly: <p>No market-moving news today.</p>

    Articles:
    {articles_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return strip_markdown_fences(response.choices[0].message.content)
    except Exception as e:
        print(f"AI generation failed for {company}: {e}")
        return "<p>Error analyzing news via AI.</p>"


def send_html_email(html_content: str, company_count: int) -> None:
    """Sends the formatted HTML digest via Resend."""
    try:
        params = {
            "from": FROM_EMAIL,
            "to": TO_EMAIL,
            "subject": f"Daily Market News Digest — {company_count} companies",
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
        ai_summary = ai_filter_and_summarize(company, raw_news)
        sections.append({"company": company, "summary_html": ai_summary})

    email_body = build_digest_email(sections, company_count=len(companies))
    send_html_email(email_body, company_count=len(companies))
