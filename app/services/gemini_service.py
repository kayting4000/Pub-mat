import json
from datetime import datetime

from google import genai

from app.core.config import settings
from app.core.database_mongo import get_mongo_db

client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def evaluate_draft(data: dict) -> dict:
    """
    Evaluates a pubmat draft and returns structured JSON:
    {
      "score": int (0-100),
      "summary": str,
      "strengths": list[str],
      "concerns": list[str],
      "recommendation": "approve" | "reject"
    }
    """
    prompt = f"""
You are an editorial AI evaluator for a publication management system.
Analyze the following article draft and return ONLY valid JSON matching this schema exactly:
{{
  "score": <int 0-100>,
  "summary": "<one sentence editorial assessment>",
  "strengths": ["<item>", ...],
  "concerns": ["<item>", ...],
  "recommendation": "<approve|reject>"
}}

Draft Data: {json.dumps(data, default=str)}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw.strip())

    db = get_mongo_db()
    await db["ai_logs"].insert_one({
        "entity_type": "draft",
        "input_data": data,
        "raw_prompt": prompt,
        "raw_response": response.text,
        "parsed_result": result,
        "logged_at": datetime.utcnow(),
    })

    return result
