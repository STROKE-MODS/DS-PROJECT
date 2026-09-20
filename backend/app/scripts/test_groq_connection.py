from __future__ import annotations

import json
import sys

import httpx

from app.core.config import settings
from app.nlp.explanation import GROQ_ENDPOINT, GROQ_MODEL


def main() -> int:
    key = settings.GROQ_API_KEY
    print(f"key_configured={bool(key)}")
    print(f"key_length={len(key or '')}")
    print(f"endpoint={GROQ_ENDPOINT}")
    print(f"model={GROQ_MODEL}")
    if not key:
        print("ERROR: GROQ_API_KEY is missing or empty in the loaded environment.")
        return 2

    body = {
        "model": GROQ_MODEL,
        "temperature": 0.2,
        "max_completion_tokens": 80,
        "messages": [
            {"role": "system", "content": "You write concise, factual internship explanations."},
            {"role": "user", "content": "In one sentence, explain why Python is useful for a data internship."},
        ],
    }
    print("request_body=" + json.dumps(body, ensure_ascii=False))
    try:
        response = httpx.post(
            GROQ_ENDPOINT,
            headers={"Authorization": f"Bearer {key}"},
            json=body,
            timeout=5.0,
        )
        print(f"http_status={response.status_code}")
        print("response_body=" + response.text[:10000])
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            print("ERROR: response JSON did not contain non-empty choices[0].message.content")
            return 3
        print("generated_text=" + content.strip())
        return 0
    except Exception as exc:
        print(f"exception_type={type(exc).__name__}")
        print(f"exception_message={exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
