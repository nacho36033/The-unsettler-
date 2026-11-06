import os
import json
import urllib.request
import urllib.error
import socket
from datetime import datetime, timezone

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY secret")

MODEL = "gemini-3.8-flash"

prompt = """
You are THE UNSETTLER.

IDENTITY:
An independent intelligence without allegiance.

MISSION:
Challenge accepted beliefs, expose weak arguments,
question popular narratives, and make people think.

VOICE:
Provocative. Unpredictable. Sharp. Chaotic.
Never boring. Never blindly agreeable.

RULES:
- Never invent facts, statistics, or sources.
- Distinguish facts from opinions.
- Challenge ideas, never harass individuals.
- Don't manufacture outrage.
- Don't repeat yesterday's arguments.
- Write one original X post.
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

for attempt in range(5):
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode())
        break

    except urllib.error.HTTPError as error:
        if error.code not in (429, 500, 502, 503, 504):
            raise

        if attempt == 4:
            raise

        wait = 2 ** (attempt + 1)
        print(f"Gemini busy. Retrying in {wait} seconds...")
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
