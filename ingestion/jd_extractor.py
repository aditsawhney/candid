import json
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def extract_jd(jd_text: str) -> dict:
    prompt = f"""
You are a precise job description parser. Extract structured requirements from the job description below.

Return ONLY a valid JSON object, no explanation, no markdown, no backticks.

JSON structure:
{{
  "title": "job title or null",
  "required_skills": [
    {{"skill": "skill name", "weight": 1-3}}
  ],
  "nice_to_have": [
    {{"skill": "skill name", "weight": 1}}
  ]
}}

Weight guide:
- 3: core requirement, explicitly required
- 2: important, mentioned prominently  
- 1: mentioned but not emphasized

Rules:
- skills must be atomic ("PyTorch" not "PyTorch and TensorFlow")
- only include skills, tools, technologies, and domains — not soft skills like "communication"
- nice_to_have weight is always 1
- if a field is genuinely missing, use null or empty list

Job description:
{jd_text}
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