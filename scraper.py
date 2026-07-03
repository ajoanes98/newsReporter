import os
import xml.etree.ElementTree as ET
import requests
import resend
from openai import OpenAI
#from dotenv import load_dotenv

# Load local .env file if it exists (for local testing)
#load_dotenv()

# Configuration
COMPANIES = ["Apple (AAPL)", "Microsoft (MSFT)", "NVIDIA (NVDA)", "Tesla (TSLA)"]
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
resend.api_key = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = "onboarding@resend.dev" # Resend gives you this default domain to test instantly!
TO_EMAIL = os.environ.get("TO_EMAIL")


def fetch_news_rss(company):
    """Fetches recent news items from Google News RSS."""
    clean_query = company.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={clean_query}+stock+when:24h&hl=en-US&gl=US&ceid=US:en"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        articles = []
        # Gather up to 8 raw items to feed into the AI filter
        for item in root.findall('.//item')[:8]:
            articles.append({
                "title": item.find('title').text,
                "link": item.find('link').text
            })
        return articles
    except Exception as e:
        print(f"Error fetching news for {company}: {e}")
        return []


def ai_filter_and_summarize(company, articles):
    """Uses OpenAI to filter out fluff and write a brief financial summary."""
    if not articles:
        return "<p>No news found in the last 24 hours.</p>"

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Format raw articles into a readable string for the prompt
    articles_text = "\n".join([f"- Title: {a['title']} | Link: {a['link']}" for a in articles])

    prompt = f"""
    You are an expert financial analyst. Below is a raw list of news articles from the last 24 hours regarding {company}.
    Your job is to ignore general product reviews, lifestyle fluff, or spam, and extract only critical, market-moving news (e.g., earnings, executive changes, regulatory issues, major macroeconomic shifts).

    Format your response in clean HTML (wrapped in a <ul> list). Provide a 1-sentence bullet point summary for each relevant piece of news, and hyper-link the title using the provided Link.
    If none of the articles are financially relevant, return exactly: "<p>No market-moving news today.</p>"

    Articles:
    {articles_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-efficient and fast
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI generation failed for {company}: {e}")
        return "<p>Error analyzing news via AI.</p>"


def send_html_email(html_content):
    """Sends the formatted HTML digest via Resend."""
    try:
        params = {
            "from": FROM_EMAIL,
            "to": TO_EMAIL,
            "subject": "🚀 Daily AI Market News Digest",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"Email sent successfully via Resend! ID: {email['id']}")
    except Exception as e:
        print(f"Failed to send email via Resend: {e}")


if __name__ == "__main__":
    print("Starting daily market news scrape...")
    email_body = "<h2>Daily Market News Briefing</h2><hr>"

    for company in COMPANIES:
        print(f"Processing {company}...")
        raw_news = fetch_news_rss(company)
        ai_summary = ai_filter_and_summarize(company, raw_news)

        email_body += f"<h3>{company}</h3>"
        email_body += ai_summary
        email_body += "<br>"

    email_body += "<p style='font-size:12px;color:gray;'>Automated via GitHub Actions.</p>"

    send_html_email(email_body)
