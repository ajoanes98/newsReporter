import os
from datetime import datetime, timezone

from config import URGENT_PRIORITY_THRESHOLD

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


def _post_slack(blocks: list[dict], fallback_text: str) -> bool:
    import requests

    if not SLACK_WEBHOOK_URL:
        print("SLACK_WEBHOOK_URL not set; skipping Slack notification.")
        return False

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json={"blocks": blocks, "text": fallback_text},
            timeout=10,
        )
        if response.status_code != 200:
            print(f"Slack webhook failed ({response.status_code}): {response.text}")
            return False
        print("Slack notification sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send Slack notification: {e}")
        return False


def _urgency_emoji(urgency: str) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(urgency.lower(), "⚪")


def _section_block(company: str, section: dict, rank: int | None = None) -> list[dict]:
    prefix = f"*{rank}. " if rank else ""
    score = section.get("priority_score", 0)
    urgency = section.get("urgency", "medium")
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{prefix}*{company}* — Priority {score}/100 "
                    f"{_urgency_emoji(urgency)} {urgency.title()}"
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Why now:* {section.get('why_now', 'N/A')}\n"
                    f"*Action:* {section.get('recommended_action', 'N/A')}\n"
                    f"*Talking point:* {section.get('talking_point', 'N/A')}"
                ),
            },
        },
    ]
    if section.get("signal_type"):
        blocks[1]["text"]["text"] = (
            f"*Signal:* {section['signal_type'].replace('_', ' ').title()}\n"
            + blocks[1]["text"]["text"]
        )
    return blocks


def send_urgent_alerts(sections: list[dict]) -> bool:
    """Post same-day urgent outreach alerts for priority >= threshold."""
    urgent = [
        s for s in sections
        if s.get("priority_score", 0) >= URGENT_PRIORITY_THRESHOLD
    ]
    if not urgent:
        print("No urgent accounts (priority >= 90); skipping Slack alert.")
        return False

    urgent.sort(key=lambda s: s.get("priority_score", 0), reverse=True)
    date_str = datetime.now(timezone.utc).strftime("%A, %B %d")
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 Urgent Port Outreach — {date_str}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{len(urgent)} account(s)* crossed the priority "
                    f"{URGENT_PRIORITY_THRESHOLD}+ threshold. Reach out today."
                ),
            },
        },
        {"type": "divider"},
    ]

    for section in urgent:
        blocks.extend(_section_block(section["company"], section))
        blocks.append({"type": "divider"})

    fallback = f"Urgent Port outreach: {len(urgent)} account(s) need attention today."
    return _post_slack(blocks, fallback)


def send_weekly_outreach(sections: list[dict], top_n: int = 5) -> bool:
    """Post the top-priority accounts to reach out to this week."""
    if not sections:
        print("No companies with news; skipping weekly Slack outreach.")
        return False

    ranked = sorted(
        sections,
        key=lambda s: s.get("priority_score", 0),
        reverse=True,
    )[:top_n]

    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📌 Port Weekly Outreach — Week of {date_str}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"Top *{len(ranked)}* accounts to prioritize this week "
                    f"based on news signals and deal timing."
                ),
            },
        },
        {"type": "divider"},
    ]

    for index, section in enumerate(ranked, start=1):
        blocks.extend(_section_block(section["company"], section, rank=index))
        blocks.append({"type": "divider"})

    companies = ", ".join(s["company"] for s in ranked)
    fallback = f"Port weekly outreach top {len(ranked)}: {companies}"
    return _post_slack(blocks, fallback)


def format_slack_preview(sections: list[dict], *, weekly: bool = False, top_n: int = 5) -> str:
    """Plain-text preview of Slack messages for local demo output."""
    lines: list[str] = []

    if weekly:
        ranked = sorted(sections, key=lambda s: s.get("priority_score", 0), reverse=True)[:top_n]
        lines.append("📌 PORT WEEKLY OUTREACH (preview)")
        lines.append("")
        for index, section in enumerate(ranked, start=1):
            lines.extend(_format_section_text(section, rank=index))
            lines.append("")
    else:
        urgent = [s for s in sections if s.get("priority_score", 0) >= URGENT_PRIORITY_THRESHOLD]
        lines.append("🚨 URGENT PORT OUTREACH (preview)")
        lines.append("")
        for section in urgent:
            lines.extend(_format_section_text(section))
            lines.append("")

    return "\n".join(lines).strip()


def _format_section_text(section: dict, rank: int | None = None) -> list[str]:
    prefix = f"{rank}. " if rank else "• "
    company = section["company"]
    score = section.get("priority_score", 0)
    urgency = section.get("urgency", "medium")
    return [
        f"{prefix}{company} — Priority {score}/100 ({urgency})",
        f"  Signal: {section.get('signal_type', 'N/A')}",
        f"  Why now: {section.get('why_now', 'N/A')}",
        f"  Action: {section.get('recommended_action', 'N/A')}",
        f"  Talking point: {section.get('talking_point', 'N/A')}",
    ]
