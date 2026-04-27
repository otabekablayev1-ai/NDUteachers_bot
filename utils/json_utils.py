import json
import re

def safe_json_load(text):
    try:
        return json.loads(text)
    except:
        pass

    text = text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        text = match.group(0)

    text = re.sub(r",\s*]", "]", text)

    try:
        return json.loads(text)
    except Exception as e:
        print("❌ JSON tuzatib ham bo‘lmadi:", e)
        return {}