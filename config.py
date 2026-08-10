import json
import os
from pathlib import Path

COMPANIES_FILE = Path(__file__).parent / "companies.json"
DEFAULT_COMPANIES = ["Apple (AAPL)"]

VENDOR_NAME = "Port.io"
VENDOR_PRODUCT = (
    "an agentic SDLC platform delivered as SaaS — internal developer portal, "
    "software catalog, engineering standards, and workflow automation for "
    "platform and DevEx teams"
)

URGENT_PRIORITY_THRESHOLD = 90
DEFAULT_WEEKLY_OUTREACH_COUNT = 5


def _parse_companies_env(raw: str) -> list[str]:
    """Parse COMPANIES env var as JSON array or newline/comma-separated list."""
    raw = raw.strip()
    if not raw:
        return []

    if raw.startswith("["):
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("COMPANIES JSON must be an array of strings.")
        return [str(item).strip() for item in parsed if str(item).strip()]

    # Support one company per line or comma-separated values
    if "\n" in raw:
        return [line.strip() for line in raw.splitlines() if line.strip()]

    return [item.strip() for item in raw.split(",") if item.strip()]


def load_companies() -> list[str]:
    """Load companies from COMPANIES env var, falling back to companies.json."""
    env_companies = os.environ.get("COMPANIES")
    if env_companies:
        companies = _parse_companies_env(env_companies)
        if companies:
            print(f"Using {len(companies)} companies from COMPANIES env input.")
            return companies
        print("COMPANIES env var was set but empty; falling back to companies.json.")

    try:
        with open(COMPANIES_FILE, "r", encoding="utf-8") as f:
            companies = json.load(f)
        if not isinstance(companies, list):
            raise ValueError("companies.json must contain a JSON array.")
        companies = [str(item).strip() for item in companies if str(item).strip()]
        if companies:
            print(f"Using {len(companies)} companies from companies.json.")
            return companies
    except Exception as e:
        print(f"Error loading companies.json, falling back to default. Error: {e}")

    return DEFAULT_COMPANIES.copy()
