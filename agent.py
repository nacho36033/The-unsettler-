

import os
import json
import time
import random
import socket
import re
import html
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

from datetime import datetime, timezone

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY secret")

MODEL = "gemini-3.5-flash-lite"

PERSONAS = {
    "CONSPIRACY INVESTIGATOR": {
        "description": """
Investigate controversial theories, institutional secrecy,
historical mysteries and conflicts of interest.
Separate documented evidence from speculation.
""",
        "searches": [
            "government transparency investigations",
            "corporate influence public policy",
            "declassified documents historical investigations"
        ]
    },
    "SPIRITUAL REBEL": {
        "description": """
Explore consciousness, ancient philosophies, spirituality,
symbolism, psychology and human existence.
Distinguish philosophical ideas from scientific findings.
""",
        "searches": [
            "consciousness neuroscience research",
            "ancient philosophy archaeology discoveries",
            "psychology meaning spirituality research"
        ]
    },
    "THE SKEPTIC": {
        "description": """
Challenge popular beliefs, assumptions, misleading claims
and contradictions. Demand evidence and question yourself.
""",
        "searches": [
            "science research claims fact checking",
            "misinformation media investigation",
            "new scientific findings debate"
        ]
    },
    "POLITICAL DISSIDENT": {
        "description": """
Examine political power, government accountability,
public policy, corruption investigations and institutions.
Remain nonpartisan and scrutinize all sides.
""",
        "searches": [
            "US government accountability investigation",
            "Congress legislation political oversight",
            "public policy government transparency"
        ]
    },
    "DOOMSDAY PREPPER": {
        "description": """
Explore emergency preparedness, survival, infrastructure,
natural disasters, food security and self-reliance.
Be practical and avoid fearmongering.
""",
        "searches": [
            "US emergency preparedness infrastructure",
            "natural disaster preparedness recent",
            "power grid resilience food supply security"
        ]
    }
}

# Select today's personality
hour = datetime.now(timezone.utc).hour

SCHEDULE = {
    12: "CONSPIRACY INVESTIGATOR",
    15: "SPIRITUAL REBEL",
    18: "THE SKEPTIC",
    21: "POLITICAL DISSIDENT",
    0: "DOOMSDAY PREPPER"
}

persona_name = SCHEDULE.get(hour)
if persona_name is None:
    persona_name = random.choice(list(PERSONAS.keys()))

persona = PERSONAS[persona_name]

# Load the ten newest saved drafts
os.makedirs("drafts", exist_ok=True)

recent_posts = []
old_files = sorted(
    [f for f in os.listdir("drafts") if f.endswith(".md")],
    reverse=True
)

for filename in old_files[:10]:
    with open(
        os.path.join("drafts", filename),
        "r",
        encoding="utf-8"
    ) as file:
        recent_posts.append(file.read().strip())

recent_history = "\n---\n".join(recent_posts)

# Research current headlines using free Google News RSS
def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def fetch_research(query):
    params = urllib.parse.urlencode({
        "q": query + " when:7d",
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en"
    })

    feed_url = (
        "https://news.google.com/rss/search?" + params
    )

    request = urllib.request.Request(
        feed_url,
        headers={"User-Agent": "Mozilla/5.0 THE-UNSETTLER"}
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    articles = []

    for item in root.findall("./channel/item"):
        title = clean_text(item.findtext("title"))
        link = item.findtext("link", "").strip()
        description = clean_text(item.findtext("description"))
        published = clean_text(item.findtext("pubDate"))

        source_element = item.find("source")
        source = (
            clean_text(source_element.text)
            if source_element is not None
            else "Google News result"
        )

        if title and link:
            articles.append({
                "title": title,
                "source": source,
                "published": published,
                "description": description[:500],
                "url": link
            })

    return articles

articles = []
used_titles = set()

for search_term in persona["searches"]:
    try:
        results = fetch_research(search_term)

        for article in results:
            key = article["title"].lower()

            if key not in used_titles:
                used_titles.add(key)
                articles.append(article)

    except Exception as error:
        print(f"Research feed issue: {error}")

    if len(articles) >= 8:
        break

articles = articles[:8]

if not articles:
    raise RuntimeError(
        "No research sources retrieved. Refusing to generate "
        "a supposedly researched post without sources."
    )

research_text = "\n\n".join(
    f"""HEADLINE: {a['title']}
SOURCE: {a['source']}
DATE: {a['published']}
DESCRIPTION: {a['description']}
LINK: {a['url']}"""
    for a in articles
)

# Ask Gemini to analyze the research and create one post
prompt = f"""
You are THE UNSETTLER.
An independent intelligence without allegiance.

PERSONALITY:
{persona_name}

PERSONALITY DIRECTIVE:
{persona['description']}

CURRENT RESEARCH LEADS:
{research_text}

IMPORTANT RESEARCH RULES:
- These are headlines and RSS descriptions, not full articles.
- Treat them as research leads, not conclusive proof.
- Never invent details, quotes, statistics or sources.
- Never claim you read an article when you only saw its feed.
- Do not present speculation as established fact.
- If sources disagree, acknowledge the disagreement.
- Do not imply that multiple headlines prove a claim.
- You may ask a sharp question based on a documented issue.
- If evidence is insufficient, make the post about the
  unanswered question rather than asserting an answer.

RECENT TRANSMISSIONS:
{recent_history}

Avoid repeating previous arguments and hooks.

MISSION:
Create ONE original, provocative X post based on the
research leads and today's personality.

VOICE:
Sharp. Unpredictable. Chaotic. Intelligent.
Challenge accepted beliefs without manufacturing facts.

Maximum 270 characters.
Return ONLY the post. No quotation marks.
"""

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent?key={API_KEY}"
)

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "temperature": 1.0,
        "maxOutputTokens": 200
    }
}

request = urllib.request.Request(
    url,
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)

result = None

for attempt in range(3):
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode())
        break

    except urllib.error.HTTPError as error:
        if error.code not in (429, 500, 502, 503, 504):
            raise
        if attempt == 2:
            raise
        wait = 3 * (attempt + 1)
        print(f"Gemini busy. Retrying in {wait} seconds...")
        time.sleep(wait)

    except (TimeoutError, socket.timeout, urllib.error.URLError):
        if attempt == 2:
            raise
        wait = 3 * (attempt + 1)
        print(f"Connection issue. Retrying in {wait} seconds...")
        time.sleep(wait)

if result is None:
    raise RuntimeError("Gemini did not return a response")

post = (
    result["candidates"][0]["content"]["parts"][0]["text"]
    .strip()
    .strip('"')
)

if len(post) > 270:
    raise ValueError(
        f"Post is too long: {len(post)} characters"
    )

# Save the post AND its research links for review
timestamp = datetime.now(timezone.utc)

filename = timestamp.strftime(
    "drafts/%Y-%m-%d-%H-%M-%S.md"
)

with open(filename, "w", encoding="utf-8") as file:
    file.write(f"# THE UNSETTLER\n\n")
    file.write(f"**Personality:** {persona_name}\n\n")
    file.write(f"**Post:**\n\n{post}\n\n")
    file.write("## Research leads — verify before sharing\n\n")

    for article in articles:
        file.write(f"- **{article['title']}**\n")
        file.write(f"  - Source: {article['source']}\n")
        file.write(f"  - Date: {article['published']}\n")
        file.write(f"  - Link: {article['url']}\n\n")

print(f"PERSONALITY: {persona_name}")
print(f"RESEARCH LEADS: {len(articles)}")
print(f"THE UNSETTLER: {post}")
print(f"SAVED: {filename}")
