import os
import requests
from datetime import datetime

ANTHROPIC_API_KEY      = os.environ["ANTHROPIC_API_KEY"]
BEEHIIV_API_KEY        = os.environ["BEEHIIV_API_KEY"]
BEEHIIV_PUBLICATION_ID = os.environ["BEEHIIV_PUBLICATION_ID"]

TODAY     = datetime.now().strftime("%A, %B %-d, %Y")
DATE_SLUG = datetime.now().strftime("%Y-%m-%d")

SYSTEM_PROMPT = f"""You are a neutral, factual geopolitical news briefing system.
Search for the most significant geopolitical developments from the last 48 hours and
return a COMPLETE, SELF-CONTAINED HTML page. No markdown. No backticks. Raw HTML only.

The page must follow these exact requirements:

STYLE:

- <meta name="color-scheme" content="light only"> in the <head>
- <meta name="supported-color-schemes" content="light"> in the <head>
- body background: #f0f4f8 !important
- content card background: #ffffff
- All body text: color #000000 !important, font-weight: 600, font-size: 16px minimum
- Font: Georgia, serif throughout
- Accent color: #b5271e for tags, rules, and the dot
- Dark masthead (#0f0f0f) with "World Brief" in large bold white text
- color-scheme: light only on :root

LAYOUT (in this order):

1. Masthead — black background, "World Brief" title, date subtitle, red rule
1. Timestamp bar — red dot + "Compiled [DATE] · Open-source reporting"
1. Lead story — tag, headline (large bold), 3 full paragraphs of body text
1. "Also Developing" section label
1. Three secondary stories — region tag, headline, 2-3 sentence summary each
1. "Quick Hits" section label
1. Five quick hit items — bold region + one sentence each
1. Footer — dark background, source attribution

CONTENT RULES:

- Lead = biggest geopolitical story globally in last 48 hours
- 3 secondary stories = different regions, not same topic as lead
- 5 quick hits = one-liners from 5 other regions or topics
- Neutral, factual, no opinion, no commentary
- Today is {TODAY}

Return ONLY the raw HTML. Nothing before <!DOCTYPE html>. Nothing after </html>."""

USER_PROMPT = f"""Search for and compile the biggest geopolitical developments
from the last 48 hours as of {TODAY}. Cover major conflicts, diplomacy, elections,
economic crises, and security events worldwide. Return ONLY the complete HTML page."""


def generate_newsletter() -> str:
    print("Generating newsletter via Claude API…")
    res = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": USER_PROMPT}],
        },
        timeout=120,
    )
    res.raise_for_status()
    data = res.json()

    html = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            html += block["text"]

    if not html.strip():
        raise ValueError("Claude returned no HTML content")

    html = html.strip()
    if html.startswith("```"):
        html = "\n".join(html.split("\n")[1:])
    if html.endswith("```"):
        html = html.rsplit("```", 1)[0]

    print(f"Newsletter generated ({len(html)} chars)")
    return html.strip()


def publish_to_beehiiv(html: str) -> str:
    print("Publishing to Beehiiv…")
    res = requests.post(
        f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUBLICATION_ID}/posts",
        headers={
            "Authorization": f"Bearer {BEEHIIV_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "title": f"World Brief — {TODAY}",
            "body": html,
            "status": "confirmed",
            "publish_type": "immediate",
        },
        timeout=30,
    )
    res.raise_for_status()
    post = res.json().get("data", {})
    url = post.get("web_url", "")
    print(f"Published: {url}")
    return url


if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"World Brief Bot — {TODAY}")
    print(f"{'='*50}\n")
    try:
        html = generate_newsletter()
        url  = publish_to_beehiiv(html)
        print(f"\n✅ Done. Live at: {url}")
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        raise
