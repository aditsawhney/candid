import json
from groq import Groq
from config import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)


def extract_resume(raw_text: str) -> dict:
    prompt = f"""
You are a precise resume parser. Extract structured information from the resume text below.

Return ONLY a valid JSON object, no explanation, no markdown, no backticks.

JSON structure:
{{
  "name": "full name or null",
  "email": "email or null",
  "phone": "phone number or null",
  "skills": [
    {{"name": "skill name", "category": "one of: programming_language / framework / database / cloud / tool / soft_skill / domain", "confidence": 0.0-1.0}}
  ],
  "experiences": [
    {{"title": "job title", "company": "company name", "start_date": "YYYY-MM or null", "end_date": "YYYY-MM or null (use null if current)", "years_calculated": float or null, "description": "brief summary of responsibilities"}}
  ],
  "education": [
    {{"degree": "degree type e.g. B.Tech, M.S., PhD", "field": "field of study", "institution": "institution name", "graduation_year": integer or null}}
  ]
}}

Rules:
- skills must be atomic ("PyTorch" not "PyTorch and TensorFlow")
- confidence reflects how clearly the skill is demonstrated, not just mentioned
- years_calculated should be a float e.g. 2.5 (derive from dates if possible, else null)
- if a field is genuinely missing, use null — do not guess

Resume text:
{raw_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    text = response.choices[0].message.content.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(text[start:end])
        raise ValueError(f"Could not parse response as JSON: {text}")