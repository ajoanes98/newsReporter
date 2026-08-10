# newsReporter

Daily AI-powered market news digest. Fetches Google News RSS for a list of companies, filters for market-moving stories with GPT-4o-mini, and emails a styled HTML briefing via Resend.

## Company list

The scraper loads companies in this order:

1. **`COMPANIES` environment variable** (highest priority) — for one-off runs with a custom list
2. **`companies.json`** — default list used by the daily scheduled job

### `COMPANIES` format

Any of these work:

```bash
# One per line
export COMPANIES="Goldman Sachs (GS)
JPMorganChase (JPM)
Apple (AAPL)"

# Comma-separated
export COMPANIES="Goldman Sachs (GS), JPMorganChase (JPM), Apple (AAPL)"

# JSON array
export COMPANIES='["Goldman Sachs (GS)", "JPMorganChase (JPM)"]'
```

### GitHub Actions manual run

1. Go to **Actions → Daily Market News Scraper → Run workflow**
2. Optionally paste a company list in the **companies** input (one per line)
3. Leave blank to use `companies.json`

### Edit the default list

Update `companies.json` and commit to change the daily scheduled run.

## Local development

```bash
pip install -r requirements.txt

# Create a .env file with:
# OPENAI_API_KEY=...
# RESEND_API_KEY=...
# TO_EMAIL=you@example.com

# Run with default companies.json
python scraper.py

# Run with a custom list
COMPANIES="Apple (AAPL), Microsoft (MSFT)" python scraper.py
```

## Required secrets (GitHub Actions)

| Secret | Description |
|--------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `RESEND_API_KEY` | Resend API key |
| `TO_EMAIL` | Recipient email address |
| `SLACK_WEBHOOK_URL` | Incoming webhook URL for your outreach Slack channel |

## Slack outreach

The scraper posts Port sales signals to a Slack channel via an **Incoming Webhook** (not the channel URL itself).

### Setup

1. Create a Slack channel (e.g. `#port-outreach`)
2. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
3. Enable **Incoming Webhooks**, add a webhook, and select your channel
4. Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)
5. Add it as the `SLACK_WEBHOOK_URL` secret in GitHub (and in your local `.env`)

### Cadence

| Job | Schedule | What it does |
|-----|----------|--------------|
| **Daily Market News Scraper** | Every day 7:00 AM EST | Email digest + urgent Slack if any account scores **90+** |
| **Weekly Port Outreach** | Mondays 8:00 AM EST | Slack post with **top 5** accounts to reach out to this week |

### Preview locally

```bash
python generate_demo.py   # writes demo_digest.html and demo_slack.txt
```

### Manual runs

```bash
# Daily mode (email + urgent Slack)
python scraper.py

# Weekly outreach only (top 5 to Slack)
python scraper.py --weekly-outreach --top 5
```
