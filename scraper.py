import argparse
import json
import os
import re
import xml.etree.ElementTree as ET

import requests
import resend
from dotenv import load_dotenv
from openai import OpenAI

from config import (
    DEFAULT_WEEKLY_OUTREACH_COUNT,
    URGENT_PRIORITY_THRESHOLD,
    VENDOR_NAME,
    VENDOR_PRODUCT,
    load_companies,
)
from email_template import build_digest_email
from slack_notifier import send_urgent_alerts, send_weekly_outreach

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


def _clamp_priority_score(value) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 50
    return max(1, min(100, score))


def ai_filter_and_summarize(company: str, articles: list[dict]) -> dict | None:
    """Filter articles and return news, insight, and sales priority metadata.

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
    - "priority_score": integer from 1-100 rating how urgently the seller should reach out this week (90+ = drop-everything urgent, 70-89 = strong opportunity, below 50 = low/no sales angle)
    - "urgency": one of "high", "medium", or "low"
    - "signal_type": short snake_case label (e.g., buying_trigger, leadership_change, budget_risk, compliance_urgency, m_and_a, ai_initiative)
    - "why_now": plain text, 1-2 sentences on why timing matters for a Port deal
    - "recommended_action": plain text, one concrete next step for the seller
    - "talking_point": plain text, one sentence the seller can use in outreach

    If none of the articles are relevant to a Port sales motion, set news_html and insight_html to empty strings and priority_score to 0.

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
        priority_score = _clamp_priority_score(data.get("priority_score", 0))

        if not news_html or news_html == NO_NEWS_RESPONSE or priority_score == 0:
            return None

        return {
            "news_html": news_html,
            "insight_html": insight_html,
            "priority_score": priority_score,
            "urgency": str(data.get("urgency", "medium")).lower(),
            "signal_type": str(data.get("signal_type", "buying_trigger")),
            "why_now": str(data.get("why_now", "")).strip(),
            "recommended_action": str(data.get("recommended_action", "")).strip(),
            "talking_point": str(data.get("talking_point", "")).strip(),
        }
    except Exception as e:
        print(f"AI generation failed for {company}: {e}")
        return None


def collect_sections(companies: list[str]) -> list[dict]:
    sections = []
    for company in companies:
        print(f"Processing {company}...")
        raw_news = fetch_news_rss(company)
        result = ai_filter_and_summarize(company, raw_news)
        if result:
            sections.append({"company": company, **result})
            print(
                f"  → included (priority {result['priority_score']}, "
                f"{result['urgency']} urgency)"
            )
        else:
            print(f"  → no Port-relevant news; skipping.")
    return sections


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


def run_daily(sections: list[dict]) -> None:
    os.makedirs("output", exist_ok=True)
    with open("output/latest.json", "w") as f:
        json.dump(sections, f, indent=2)
        
    urgent = [s for s in sections if s.get("priority_score", 0) >= URGENT_PRIORITY_THRESHOLD]
    if urgent:
        print(f"Sending urgent Slack alert for {len(urgent)} account(s)...")
        send_urgent_alerts(sections)
    else:
        print(f"No accounts at priority {URGENT_PRIORITY_THRESHOLD}+; skipping urgent Slack.")

    if sections:
        email_body = build_digest_email(sections, news_count=len(sections))
        send_html_email(email_body, news_count=len(sections))
    else:
        print("No market-moving news today. Skipping email.")


def run_weekly_outreach(sections: list[dict], top_n: int) -> None:
    send_weekly_outreach(sections, top_n=top_n)


def main() -> None:
    parser = argparse.ArgumentParser(description="Port.io account news digest")
    parser.add_argument(
        "--weekly-outreach",
        action="store_true",
        help="Post top-priority accounts to Slack (Monday weekly job).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_WEEKLY_OUTREACH_COUNT,
        help="Number of accounts to include in weekly Slack outreach.",
    )
    args = parser.parse_args()

    companies = load_companies()
    print(f"Starting market news scrape for {len(companies)} companies...")
    sections = collect_sections(companies)

    if args.weekly_outreach:
        run_weekly_outreach(sections, top_n=args.top)
    else:
        run_daily(sections)


if __name__ == "__main__":
    main()
