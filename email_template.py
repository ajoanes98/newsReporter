from datetime import datetime, timezone


def _format_date() -> str:
    return datetime.now(timezone.utc).strftime("%A, %B %d, %Y")


def build_digest_email(sections: list[dict], company_count: int) -> str:
    """Build a styled HTML email from company news sections.

    Each section dict should have:
      - company: str
      - summary_html: str (HTML from AI, e.g. <ul> or <p>)
    """
    section_blocks = []
    for section in sections:
        company = section["company"]
        summary_html = section["summary_html"]
        section_blocks.append(
            f"""
            <tr>
              <td style="padding:0 0 20px 0;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                       style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
                  <tr>
                    <td style="background:#f8fafc;padding:14px 20px;border-bottom:1px solid #e2e8f0;">
                      <p style="margin:0;font-size:16px;font-weight:700;color:#0f172a;letter-spacing:-0.2px;">
                        {company}
                      </p>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:18px 20px;font-size:15px;line-height:1.6;color:#334155;">
                      <div class="summary-content">
                        {summary_html}
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            """
        )

    sections_html = "\n".join(section_blocks)
    date_str = _format_date()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily Market News Digest</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="max-width:640px;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#1e3a5f 0%,#0f766e 100%);padding:32px 28px;">
              <p style="margin:0 0 6px 0;font-size:12px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:rgba(255,255,255,0.75);">
                Market Intelligence
              </p>
              <h1 style="margin:0 0 8px 0;font-size:26px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">
                Daily News Digest
              </h1>
              <p style="margin:0;font-size:14px;color:rgba(255,255,255,0.85);">
                {date_str}
              </p>
            </td>
          </tr>

          <!-- Summary bar -->
          <tr>
            <td style="padding:16px 28px;background:#f8fafc;border-bottom:1px solid #e2e8f0;">
              <p style="margin:0;font-size:13px;color:#64748b;">
                Tracking <strong style="color:#0f172a;">{company_count}</strong> companies &middot;
                Last 24 hours &middot; AI-filtered for market-moving news
              </p>
            </td>
          </tr>

          <!-- Company sections -->
          <tr>
            <td style="padding:24px 28px 8px 28px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                {sections_html}
              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 28px 28px 28px;border-top:1px solid #e2e8f0;">
              <p style="margin:0;font-size:12px;line-height:1.5;color:#94a3b8;text-align:center;">
                Automated by <strong style="color:#64748b;">newsReporter</strong> via GitHub Actions.<br>
                News sourced from Google News RSS and summarized by AI.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

  <style>
    .summary-content ul {{
      margin:0;padding-left:20px;
    }}
    .summary-content li {{
      margin-bottom:10px;color:#334155;
    }}
    .summary-content li:last-child {{
      margin-bottom:0;
    }}
    .summary-content a {{
      color:#0f766e;text-decoration:none;font-weight:600;
    }}
    .summary-content a:hover {{
      text-decoration:underline;
    }}
    .summary-content p {{
      margin:0;color:#64748b;font-style:italic;
    }}
  </style>
</body>
</html>"""
