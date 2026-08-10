"""Generate demo_digest.html and demo_slack.txt for local preview."""

from email_template import build_digest_email
from slack_notifier import format_slack_preview

DEMO_SECTIONS = [
    {
        "company": "Itaú Unibanco (ITUB)",
        "priority_score": 78,
        "urgency": "medium",
        "signal_type": "buying_trigger",
        "why_now": (
            "Strong earnings reduce procurement friction for platform investments "
            "in the next quarter."
        ),
        "recommended_action": (
            "Engage VP Engineering or Head of Platform Engineering about "
            "standardizing service ownership and SDLC workflows."
        ),
        "talking_point": (
            "Position Port as the way to accelerate safe software delivery "
            "across growing product teams without adding operational overhead."
        ),
        "news_html": (
            "<ul>"
            "<li><a href=\"https://example.com/itau-earnings\">"
            "Itaú Unibanco Posts Strong 2Q26 Earnings with Robust Credit Growth"
            "</a> — Strong results suggest engineering teams may have budget "
            "to invest in developer experience tooling like Port.</li>"
            "</ul>"
        ),
        "insight_html": (
            "<p>Favorable earnings reduce procurement friction for platform "
            "investments in the next quarter. Position Port as a way to "
            "accelerate safe software delivery across growing product teams.</p>"
        ),
    },
    {
        "company": "Goldman Sachs (GS)",
        "priority_score": 94,
        "urgency": "high",
        "signal_type": "ai_initiative",
        "why_now": (
            "AI tooling expansion creates budget and executive attention on "
            "engineering productivity, while regulatory scrutiny adds urgency "
            "for governed SDLC workflows."
        ),
        "recommended_action": (
            "Multi-thread Platform Engineering and compliance-aware engineering "
            "leaders; propose a catalog + scorecards pilot."
        ),
        "talking_point": (
            "Frame Port as the control plane connecting services, standards, "
            "and automation — not another point tool."
        ),
        "news_html": (
            "<ul>"
            "<li><a href=\"https://example.com/gs-engineering\">"
            "Goldman Sachs Expands Internal AI Tooling for Developer Teams"
            "</a> — Active investment in developer platform modernization "
            "is a strong entry point for Port's agentic SDLC capabilities.</li>"
            "<li><a href=\"https://example.com/gs-compliance\">"
            "Regulators Increase Scrutiny on Financial Services Software Controls"
            "</a> — Compliance pressure increases urgency for engineering "
            "standards and catalog governance.</li>"
            "</ul>"
        ),
        "insight_html": (
            "<p>High-intent window: AI tooling expansion plus regulatory scrutiny "
            "makes this a priority outreach account this week.</p>"
        ),
    },
    {
        "company": "JPMorganChase (JPM)",
        "priority_score": 72,
        "urgency": "medium",
        "signal_type": "leadership_change",
        "why_now": (
            "New CTO appointment often triggers a 90-day review of developer "
            "platform and internal tooling stack."
        ),
        "recommended_action": (
            "Congratulate the new CTO and offer a Port platform briefing "
            "focused on engineering standards at scale."
        ),
        "talking_point": (
            "Help the new leadership team establish a software catalog and "
            "scorecard foundation early in their tenure."
        ),
        "news_html": (
            "<ul>"
            "<li><a href=\"https://example.com/jpm-cto\">"
            "JPMorgan Names New Chief Technology Officer"
            "</a> — Leadership change may open a window to influence "
            "developer platform strategy.</li>"
            "</ul>"
        ),
        "insight_html": (
            "<p>New CTO hires are one of the strongest triggers for internal "
            "developer portal evaluations. Reach out within the next two weeks.</p>"
        ),
    },
]


def main() -> None:
    html = build_digest_email(DEMO_SECTIONS[:2], news_count=2)
    with open("demo_digest.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Wrote demo_digest.html")

    slack_preview = (
        format_slack_preview(DEMO_SECTIONS, weekly=True, top_n=3)
        + "\n\n"
        + "─" * 50
        + "\n\n"
        + format_slack_preview(DEMO_SECTIONS, weekly=False)
    )
    with open("demo_slack.txt", "w", encoding="utf-8") as f:
        f.write(slack_preview)
    print("Wrote demo_slack.txt")


if __name__ == "__main__":
    main()
