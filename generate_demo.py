"""Generate demo_digest.html for local preview without running the workflow."""

from email_template import build_digest_email

DEMO_SECTIONS = [
    {
        "company": "Itaú Unibanco (ITUB)",
        "news_html": (
            "<ul>"
            "<li><a href=\"https://example.com/itau-earnings\">"
            "Itaú Unibanco Posts Strong 2Q26 Earnings with Robust Credit Growth"
            "</a> — Strong results suggest engineering and platform teams may "
            "have budget to invest in developer experience tooling like Port as "
            "they scale digital banking products.</li>"
            "</ul>"
        ),
        "insight_html": (
            "<p>Favorable earnings reduce procurement friction for platform "
            "investments in the next quarter. Position Port as a way to "
            "accelerate safe software delivery across growing product teams "
            "without adding operational overhead.</p>"
            "<p>Engage the VP Engineering or Head of Platform Engineering with "
            "a message tied to scaling developer self-service and catalog "
            "governance. Ask whether Q3 priorities include standardizing "
            "service ownership and SDLC workflows across business units.</p>"
        ),
    },
    {
        "company": "Goldman Sachs (GS)",
        "news_html": (
            "<ul>"
            "<li><a href=\"https://example.com/gs-engineering\">"
            "Goldman Sachs Expands Internal AI Tooling for Developer Teams"
            "</a> — A push to embed AI across engineering workflows signals "
            "active investment in developer platform modernization — a strong "
            "entry point for Port's agentic SDLC capabilities.</li>"
            "<li><a href=\"https://example.com/gs-compliance\">"
            "Regulators Increase Scrutiny on Financial Services Software Controls"
            "</a> — Heightened compliance pressure increases urgency for "
            "engineering standards, auditability, and catalog governance that "
            "Port scorecards and workflows can support.</li>"
            "</ul>"
        ),
        "insight_html": (
            "<p>This is a high-intent window: AI tooling expansion creates "
            "budget and executive attention on engineering productivity, while "
            "regulatory scrutiny adds urgency for governed SDLC workflows. "
            "Frame Port as the control plane that connects services, standards, "
            "and automation — not another point tool.</p>"
            "<p>Multi-thread across Platform Engineering and compliance-aware "
            "engineering leaders. Lead with a pilot scoped to one domain "
            "(e.g., service catalog + scorecards) to align with their AI and "
            "governance initiatives simultaneously.</p>"
        ),
    },
]


def main() -> None:
    html = build_digest_email(DEMO_SECTIONS, news_count=len(DEMO_SECTIONS))
    output_path = "demo_digest.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
