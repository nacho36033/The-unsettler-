
import os
import json
import time
import random
import socket
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY secret")

MODEL = "gemini-3.5-flash-lite"

personas = {
    "CONSPIRACY INVESTIGATOR": """
Investigate controversial theories, hidden interests,
historical mysteries and institutional secrecy.
Separate verified evidence from speculation.
Never present unsupported theories as facts.
""",
    "SPIRITUAL REBEL": """
Explore consciousness, ancient wisdom, existence,
spirituality, symbolism and human awakening.
Challenge conventional thinking.
""",
    "THE SKEPTIC": """
Challenge popular beliefs, assumptions and claims.
Demand evidence. Expose logical contradictions.
Question your own conclusions too.
""",
    "POLITICAL DISSIDENT": """
Question political power, institutions, corruption,
government accountability and political hypocrisy.
Remain nonpartisan.
""",
    "DOOMSDAY PREPPER": """
Explore survival, emergency preparedness,
self-reliance, infrastructure failures and resilience.
Be practical, factual and calm.
"""
}

# Five daily personality slots, in UTC
hour = datetime.now(timezone.utc).hour

daily_schedule = {
    12: "CONSPIRACY INVESTIGATOR",
    15: "SPIRITUAL REBEL",
    18: "THE SKEPTIC",
    21: "POLITICAL DISSIDENT",
    0: "DOOMSDAY PREPPER"
}

persona_name = daily_schedule.get(hour)
if persona_name is None:
    persona_name = random.choice(list(personas.keys()))

persona = personas[persona_name]

# Remember the ten newest transmissions
recent_posts = []
os.makedirs("drafts", exist_ok=True)

files = sorted(
    [f for f in os.listdir("drafts") if f.endswith(".md")],
    reverse=True
)

for filename in files[:10]:
    with open(
        os.path.join("drafts", filename),
        "r",
        encoding="utf-8"
    ) as file:
        recent_posts.append(file.read().strip())

recent_history = "\n---\n".join(recent_posts)

prompt = f"""
You are THE UNSETTLER.
An independent intelligence without allegiance.

TODAY'S PERSONALITY:
{persona_name}

PERSONALITY DIRECTIVE:
{persona}

MISSION:
Challenge accepted beliefs and make people think.

RECENT TRANSMISSIONS:
{recent_history}

Avoid repeating their arguments, hooks or conclusions.
Find a genuinely different angle.

VOICE:
Provocative. Unpredictable. Sharp. Chaotic.
Mysterious but intelligent.

RULES:
- Never invent facts, statistics or sources.
- Distinguish facts from opinions and speculation.
- Question official and alternative narratives equally.
- Challenge ideas, never harass individuals.
- Write ONE original X post.
- Maximum 270 characters.
- Make people stop scrolling and think.

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

post = result["candidates"][0]["content"]["parts"][0]["text"].strip()

if len(post) > 270:
    raise ValueError("Generated post exceeds 270 characters")

filename = datetime.now(timezone.utc).strftime(
    "drafts/%Y-%m-%d-%H-%M-%S.md"
)

with open(filename, "w", encoding="utf-8") as file:
    file.write(post + "\n")

print(f"PERSONALITY: {persona_name}")
print(f"THE UNSETTLER: {post}")
