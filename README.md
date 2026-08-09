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
