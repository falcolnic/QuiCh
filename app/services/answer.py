from json import load
import logging
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

log = logging.getLogger(__name__)


def answer_question(term, res):
    docs = ["<document>" + d.idea + "</document>\n" for d, _ in res]
    client = anthropic.Anthropic(api_key=anthropic_api_key, max_retries=3)
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""
Answer the question using only relevant information from the provided context. 
Ignore any irrelevant documents.
If the context is entirely unrelated to the question, respond with:
```txt
I can’t answer your question
```

Ensure your response is clear, concise, and aligned with the relevant context.

Context: 
{docs} 

Question: {term} 

Answer:""",
                    }
                ],
            },
        ],
    )
    response = response.content[0].text
    log.info("Question answered: %s", response)
    return response