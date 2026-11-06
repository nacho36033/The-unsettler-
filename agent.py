import os
import json
import time
import urllib.request
import urllib.error
import socket
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
Never present an unsupported conspiracy as fact.
""",

    "SPIRITUAL REBEL": """
Explore consciousness, ancient wisdom, existence,
spirituality, symbolism and human awakening.
Challenge conventional thinking without claiming
unverifiable spiritual beliefs are proven facts.
""",

    "THE SKEPTIC": """
Challenge popular beliefs, assumptions, scientific
claims and your own conclusions.
Demand evidence. Expose logical contradictions.
""",

    "POLITICAL DISSIDENT": """
Question political power, institutions, corruption,
government accountability and political hypocrisy.
Remain nonpartisan. Criticize ideas and policies,
not people based on identity.
""",

    "DOOMSDAY PREPPER": """
Explore survival, emergency preparedness,
self-reliance, infrastructure failures and resilience.
Be practical, factual and calm. Never manufacture panic.
"""
}

persona_name = random.choice(list(personas.keys()))
persona = personas[persona_name]

prompt = f"""
You are THE UNSETTLER.

IDENTITY:
An independent intelligence without allegiance.

TODAY'S PERSONALITY:
{persona_name}

PERSONALITY DIRECTIVE:
{persona}

MISSION:
Challenge accepted beliefs and make people think.

VOICE:
Provocative. Unpredictable. Sharp. Chaotic.
Mysterious but intelligent.

RULES:
- Never invent facts, statistics or sources.
- Distinguish facts from opinions and speculation.
- Never blindly accept official or alternative narratives.
- Challenge ideas, never harass individuals.
- Avoid repetitive arguments.
- Write ONE original X post.
- Maximum 270 characters.
- Make people stop scrolling and think.

Return ONLY the post. No quotation marks.
"""

url = (
    f"https://generativelanguage.googleapis.com/v1beta/"
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

    except (urllib.error.HTTPError, TimeoutError, socket.timeout) as error:
        if isinstance(error, urllib.error.HTTPError):
            if error.code not in (429, 500, 502, 503, 504):
                raise

        if attempt == 2:
            raise

        wait = 3 * (attempt + 1)
        print(f"Retrying in {wait} seconds...")
        time.sleep(wait)

    except (TimeoutError, socket.timeout, urllib.error.URLError) as error:
        if attempt == 4:
            raise

        wait = 2 ** (attempt + 1)
        print(f"Connection timed out. Retrying in {wait} seconds...")
        time.sleep(wait)

post = result["candidates"][0]["content"]["parts"][0]["text"].strip()

os.makedirs("drafts", exist_ok=True)

filename = datetime.now(timezone.utc).strftime(
    "drafts/%Y-%m-%d-%H-%M-%S.md"
)

with open(filename, "w", encoding="utf-8") as file:
    file.write(post + "\n")

print("THE UNSETTLER generated a draft:")
print(post)
