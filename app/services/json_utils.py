import json
import logging
import os
from json import JSONDecodeError

import anthropic

log = logging.getLogger(__name__)
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")


def is_json(docs):
    try:
        json.loads(docs)
        return True
    except JSONDecodeError:
        return False


def fix_json_hook(response):
    if isinstance(response.content[0].input["items"], str):
        log.error("INVALID: %s", response.content[0].input["items"])
        docs = normalize_json(response.content[0].input["items"])
        if is_json(docs):
            response.content[0].input["items"] = docs
            log.info("JSON FIXED")
            return response

        docs = fix_json(docs)
        if is_json(docs):
            response.content[0].input["items"] = docs
            log.info("JSON FIXED")
            return response

    return response


def error_json_hook(response):
    log.error("ERROR HOOK: %s", response)


def fix_json(document):
    client = anthropic.Anthropic(api_key=anthropic_api_key, max_retries=10)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""FIX THE GIVEN JSON:
```json
{document}
``` 
Only output the valid JSON format, otherwise the system will break.
Escape all double quotes. BUT: Single quotes should not be escaped.
Before returning the result double check does JSON syntax is correct.
    """,
                    }
                ],
            },
            {"role": "assistant", "content": "Here is the JSON requested:"},
        ],
        # extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
    )

    return normalize_json(response.content[0].text)


def normalize_json(response_text):
    return response_text.replace("\\'", "'")