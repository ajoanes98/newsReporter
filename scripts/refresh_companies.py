"""Rebuild companies.json from Anthony's active HubSpot deals.

Rule: every open deal where Leading SE = Anthony (owner 90493000) and the deal
was modified in the last LOOKBACK_DAYS days. Ticker suffixes like "(ITUB)" that
already exist in companies.json are preserved, because HubSpot doesn't store
them and the news search works better with them.
"""
import json, os, re, sys, datetime as dt, pathlib, requests

HUBSPOT = "https://api.hubapi.com"
ANTHONY_OWNER_ID = "90493000"
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS", "30"))
SUFFIXES = re.compile(r"\s*[-–]\s*(expansion|renewal|upsell|poc|[\d,]+)\s*$", re.I)

def hs(path: str, body: dict) -> dict:
    r = requests.post(f"{HUBSPOT}{path}", json=body, timeout=30,
                      headers={"Authorization": f"Bearer {os.environ['HUBSPOT_TOKEN']}"})
    r.raise_for_status()
    return r.json()

def active_deals() -> list[dict]:
    since = int((dt.datetime.utcnow() - dt.timedelta(days=LOOKBACK_DAYS)).timestamp() * 1000)
    body = {"filterGroups": [{"filters": [
                {"propertyName": "leading_se", "operator": "EQ", "value": ANTHONY_OWNER_ID},
                {"propertyName": "hs_is_closed", "operator": "EQ", "value": "false"},
                {"propertyName": "hs_lastmodifieddate", "operator": "GTE", "value": str(since)}]}],
            "properties": ["dealname"], "limit": 100}
    deals, after = [], None
    while True:
        if after: body["after"] = after
        page = hs("/crm/v3/objects/deals/search", body)
        deals += page["results"]
        after = page.get("paging", {}).get("next", {}).get("after")
        if not after: return deals

def company_names(deal_ids: list[str]) -> set[str]:
    """Prefer the associated company's name; fall back to the cleaned deal name."""
    names = set()
    assoc = hs("/crm/v4/associations/deals/companies/batch/read",
               {"inputs": [{"id": d} for d in deal_ids]})
    company_ids = {t["toObjectId"] for r in assoc.get("results", []) for t in r.get("to", [])}
    if company_ids:
        comps = hs("/crm/v3/objects/companies/batch/read",
                   {"inputs": [{"id": str(c)} for c in company_ids], "properties": ["name"]})
        names |= {c["properties"]["name"].strip() for c in comps["results"] if c["properties"].get("name")}
    return names

def main() -> None:
    path = pathlib.Path("companies.json")
    existing = json.loads(path.read_text()) if path.exists() else []
    # "Itaú Unibanco (ITUB)" -> key "itaú unibanco", keeps the ticker form
    by_base = {re.sub(r"\s*\(.*?\)\s*$", "", e).lower(): e for e in existing}

    deals = active_deals()
    names = company_names([d["id"] for d in deals]) if deals else set()
    if not names:
        names = {SUFFIXES.sub("", d["properties"]["dealname"]).strip() for d in deals}

    out = sorted({by_base.get(n.lower(), n) for n in names}, key=str.lower)
    if not out:
        sys.exit("No active deals found; refusing to wipe companies.json")
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    added, removed = set(out) - set(existing), set(existing) - set(out)
    print(f"{len(out)} companies | +{len(added)} {sorted(added)} | -{len(removed)} {sorted(removed)}")

if __name__ == "__main__":
    main()
