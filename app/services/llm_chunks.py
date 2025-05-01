import json
import logging
import os
import re
from json import JSONDecodeError

import anthropic
import instructor
from dotenv import load_dotenv

from app.services.document_schema import DocumentListSchema

load_dotenv()
log = logging.getLogger(__name__)


anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
anthropic_client = instructor.from_anthropic(anthropic_client)


def is_json(docs):
    try:
        json.loads(docs)
        return True
    except JSONDecodeError:
        return False


def fix_json_hook(response):
    if isinstance(response.content[0].input["docs"], str):
        log.error("INVALID: %s", response.content[0].input["docs"])
        docs = normalize_json(response.content[0].input["docs"])
        if is_json(docs):
            response.content[0].input["docs"] = docs
            log.info("JSON FIXED")
            return response

        docs = fix_json(docs)
        if is_json(docs):
            response.content[0].input["docs"] = docs
            log.info("JSON FIXED")
            return response

    return response


def error_json_hook(response):
    log.error("ERROR HOOK: %s", response)


anthropic_client.on("completion:response", fix_json_hook)
anthropic_client.on("completion:error", error_json_hook)


def split_document(llm_chunks, document):
    times = {c["start"] for c in llm_chunks}
    if len(times) != len(llm_chunks):
        log.error("LLM chunks mismatch %s", json.dumps(llm_chunks))
        return []
    regex_patter = "|".join([f"\[{c['start']}s\]" for c in llm_chunks[1:]])
    docs = re.split(regex_patter, document)

    if len(docs) != len(llm_chunks):
        log.error(
            f"Invalid number of chunks. Expected {len(llm_chunks)} but got {len(docs)}"
        )
        return []

    for doc, c in zip(docs, llm_chunks):
        log.info(f"Chunk title: [{c['start']}] {c['title']}")
        c["text"] = doc

    return docs


def split_transcript_document(document) -> DocumentListSchema:
    response, completion = anthropic_client.messages.create_with_completion(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are given an audio transcription. Where each phrase has a timestamp in seconds.
# Instructions:

- Split the transcript into chunks based on context (not exceeding 5 chunks).
- To ensure accuracy, please read the text carefully and pay attention to important pieces.
- Provide the output in valid JSON format using the schema below:

```json
{{
    "title": string, // A short, clear title summarizing the chunk.
    "start": integer, // The start time of the first chunk in seconds. Make sure that timestamp exist in the document 
    "end": integer, // The end time of the last chunk in seconds. Make sure that timestamp exist in the document 
    "context": string  // A short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
}}
```
IMPORTANT: every time double check `start` and `end` value to make sure it presents in the given document!!!
In case if you pick and invalid timestamp, please review your findings.

Given transcript:
<transcript>{document}\n</transcript>"
""",
            }
        ],
        response_model=DocumentListSchema,
    )

    return response, {
        "output_tokens": completion.usage.output_tokens,
        "input_tokens": completion.usage.input_tokens,
    }


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
            {
                "role": "assistant",
                "content": "Here is the JSON requested:",
            },
        ],
    )

    return normalize_json(response.content[0].text)


def normalize_json(response_text):
    return response_text.replace("\\'", "'")
