"""Post demo outreach data to Slack to verify webhook configuration."""

from generate_demo import DEMO_SECTIONS
from slack_notifier import send_weekly_outreach


def main() -> None:
    ok = send_weekly_outreach(DEMO_SECTIONS, top_n=3)
    if not ok:
        raise SystemExit(1)
    print("Slack test message sent successfully.")


if __name__ == "__main__":
    main()
