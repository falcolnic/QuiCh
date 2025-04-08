import logging
import os
import uuid
from typing import Dict, List

import anthropic
from instructor import Instructor, Mode, patch
from pydantic import BaseModel

from app.database import db_session
from app.models.texts import IdeaModel
from app.services.chunker import to_text
from app.services.json_utils import error_json_hook, fix_json_hook
from app.services.transcript import load_transcript

log = logging.getLogger(__name__)

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key, max_retries=10)

anthropic_client = Instructor(
    client=anthropic_client,
    create=patch(
        create=anthropic_client.beta.messages.create,
        mode=Mode.ANTHROPIC_TOOLS,
    ),
    mode=Mode.ANTHROPIC_TOOLS,
)

INSTRUCTION = """# IDENTITY and PURPOSE

You are a wisdom extraction service for text content. 
You extract surprising, insightful, and interesting information from text content.
You are interested in insights related to hacking, bug bounty, information security, software development, programing and similar topics.

Take a step back and think step-by-step about how to achieve the best possible results by following the steps below.
You have a lot of freedom to make this work well.

# STEPS:

- Extract between 10 and 30 of the most surprising, insightful, or impactful statements, ideas, questions, or insights from the input text.
- If there are less than 30 then collect all of them.
- To maintain accuracy, note the approximate timestamp of each idea. Use timestamps from text.
- Provide the output in valid JSON format using the schema below:

```json
{{
    "text": string, // A unique, surprising, clear idea from the text
    "timestamp": integer, //  Approximate timestamp in seconds
}}
```
# OUTPUT INSTRUCTIONS

- Return a JSON list of idea with timestamps.
- Validate the JSON to ensure it is error-free, with correct syntax and escaped characters if needed.
"""

anthropic_client.on("completion:response", fix_json_hook)
anthropic_client.on("completion:error", error_json_hook)


class IdeaSchema(BaseModel):
    text: str
    timestamp: int


class IdeasListSchema(BaseModel):
    items: List[IdeaSchema]


def get_ideas(document) -> tuple[IdeasListSchema, Dict]:
    response, completion = anthropic_client.chat.completions.create_with_completion(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": INSTRUCTION,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": f"# INPUT\nGiven transcript:\n<transcript>{document}\n</transcript>",
                    },
                ],
            }
        ],
        response_model=IdeasListSchema,
    )

    return response, completion.usage.dict()


def load_ideas(videos):
    with db_session() as db:
        for video_id in videos:
            t = load_transcript(db, video_id)

            chunks = len(t.transcript) // 500
            chunk_length = int(len(t.transcript) / chunks)
            for i in range(chunks):
                log.info(
                    "ID: %s [%s/%s] Extract ideas",
                    video_id,
                    i,
                    chunks,
                )
                chunk = t.transcript[i * chunk_length : i * chunk_length + chunk_length]
                text = to_text(chunk)
                try:
                    res, _ = get_ideas(text)
                except Exception as e:
                    log.error(
                        "Something went wrong while extracting ideas: %s",
                        e,
                    )
                    continue

                db.add_all(
                    [
                        IdeaModel(
                            id=uuid.uuid4(),
                            idea=i.text,
                            start=i.timestamp,
                            video_id=video_id,
                        )
                        for i in res.items
                    ]
                )
                db.commit()
            log.info("ID: [%s] DONE Extract ideas", video_id)
