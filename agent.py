

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

# Select one research source for one focused post
selected_article = articles[0]
articles = [selected_article]

research_text = f"""
HEADLINE: {selected_article['title']}
SOURCE: {selected_article['source']}
DATE: {selected_article['published']}
DESCRIPTION: {selected_article['description']}
LINK: {selected_article['url']}
"""

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

- You only have access to the headlines and RSS descriptions below.
- Never invent scientific findings, statistics, dates,
  quotations, experiments or technical explanations.
- Never add a factual detail unless it appears explicitly
  in the supplied headline or description.
- A headline alone is not proof of the underlying claim.
- Do not turn a speculative article into an established fact.
- If the research does not support a strong factual statement,
  write a provocative QUESTION instead.
- Never imply that you read the full article.
- Never invent connections between unrelated stories.
- Separate VERIFIED FACTS, INTERPRETATIONS, and SPECULATION.
- VERIFIED FACTS must be directly supported by the supplied research lead.
- INTERPRETATIONS are reasonable conclusions, but must be presented as interpretations, not established facts.
- SPECULATION must be clearly framed as a possibility, theory, or question.
- Never present speculation as proven evidence.
- Never claim a source confirms something it does not explicitly support.
- Be provocative with questions and reasoning, not fabricated facts.
- When evidence is weak, say so instead of pretending certainty.
- Base the post on the ONE research lead supplied. Do not switch topics.
- The post must clearly relate to that lead's specific subject.
- If the headline and description do not support an interesting angle,
  write a question about that exact subject, or state that the lead
  is too thin to support a responsible post.
- Do not introduce separate scientific or historical concepts
  unless they appear in this lead's headline or description.
- Challenge both mainstream and alternative narratives.
- Be intellectually provocative, not factually reckless.
- If no defensible angle exists, say so and do not manufacture
  a claim just to create an interesting post.

RECENT TRANSMISSIONS:
{recent_history}

Avoid repeating previous arguments and hooks.

MISSION:
Create ONE original, provocative X post based on the
research leads and today's personality.

VOICE:
Sharp. Unpredictable. Chaotic. Intelligent.
Challenge accepted beliefs without manufacturing facts.

Maximum 270 characters for the X post.

Return the response in EXACTLY this format:

POST:
[One original X post]

VERIFIED FACTS:
[List only facts explicitly supported by the supplied research.
If none, write "None established from the supplied lead."]

INTERPRETATIONS:
[List reasonable interpretations and explain they are interpretations.
If none, write "None."]

SPECULATION:
[List speculative ideas, clearly identified as speculation.
If none, write "None."]

SOURCE LIMITATIONS:
[Explain what the headline and description do NOT establish.]

Do not put the private review inside the X post.
Do not invent evidence. Keep each section concise.

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent?key={API_KEY}"
)

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "temperature": 1.0,
       "maxOutputTokens": 450
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

response_text = (
    result["candidates"][0]["content"]["parts"][0]["text"]
    .strip()
)

def get_section(label):
    match = re.search(
        rf"(?ims)^{re.escape(label)}:\s*(.*?)(?=^(?:POST|VERIFIED FACTS|INTERPRETATIONS|SPECULATION|SOURCE LIMITATIONS):|\Z)",
        response_text
    )
    return match.group(1).strip() if match else "Not provided."

post = get_section("POST").strip().strip('"')

verified_facts = get_section("VERIFIED FACTS")
interpretations = get_section("INTERPRETATIONS")
speculation = get_section("SPECULATION")
source_limitations = get_section("SOURCE LIMITATIONS")

if post == "Not provided.":
    raise ValueError("Gemini did not return a valid X post.")

if len(post) > 270:
    raise ValueError(
        f"Post is too long: {len(post)} characters"
    )
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
