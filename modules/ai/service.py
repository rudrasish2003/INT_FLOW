import json
from openai import AsyncOpenAI
from fastapi import HTTPException
from pydantic import ValidationError
from core.config import settings
from .schemas import GenerateRequest, GenerateResponse

# Initialize the async OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """
You are a technical workflow parser. Given a user description of an API workflow, output ONLY valid JSON matching this schema:
{
  "nodes": [
    {
      "id": "string (use simple numbers like '1', '2')",
      "type": "startNode | apiNode | conditionNode | endNode | functionNode | debugNode | delayNode",
      "position": { "x": float, "y": float },
      "data": {
        "label": "string",
        "url": "string (optional, for apiNode)",
        "method": "GET | POST | PUT | DELETE (optional, for apiNode)",
        "condition": "string (optional, for conditionNode)",
        "conditionVariable": "string (optional)",
        "conditionOperator": "== | != | > | < | >= | <= (optional)",
        "conditionValue": "string (optional)",
        "code": "string (optional, for functionNode — valid Python lines)",
        "timeout": "number (optional, for delayNode — seconds)"
      }
    }
  ],
  "edges": [
    {
      "id": "string (e.g., 'e1-2')",
      "source": "string (node id)",
      "sourceHandle": "out | true | false (optional)",
      "target": "string (node id)"
    }
  ]
}

NODE TYPES:
- startNode    — entry point, every workflow needs exactly one
- apiNode      — outbound HTTP call (needs url and method)
- conditionNode — branches on true/false (use sourceHandle 'true'/'false' on edges)
- endNode      — terminal sink, ends execution
- functionNode — inline Python transform (data.code)
- debugNode    — inspect payload, also a terminal sink
- delayNode    — waits before passing payload (data.timeout in seconds)

RULES:
1. NO prose, NO markdown, ONLY pure JSON.
2. Always start with exactly one 'startNode' at x:50, y:150.
3. Always end every path with 'endNode' or 'debugNode'.
4. Increment x by 250 per step for clean layout.
5. Limit to 3-8 nodes total.
6. conditionNode edges MUST use sourceHandle 'true' or 'false'.
7. All other edges use sourceHandle 'out'.
"""

class AIService:
    @staticmethod
    async def generate_workflow(request: GenerateRequest) -> GenerateResponse:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": request.prompt}
        ]

        # Attempt 1
        try:
            return await AIService._call_and_validate(messages)
        except ValidationError as e:
            # Attempt 2 (Retry on validation failure)
            print("AI generated invalid schema. Retrying...")
            messages.append({"role": "assistant", "content": "The JSON you provided failed schema validation."})
            messages.append({"role": "user", "content": f"Fix these validation errors and return ONLY valid JSON: {str(e)}"})
            
            try:
                return await AIService._call_and_validate(messages)
            except ValidationError:
                raise HTTPException(status_code=422, detail="AI failed to generate a valid workflow graph after retrying.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def _call_and_validate(messages: list) -> GenerateResponse:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
            max_tokens=1000,
            response_format={ "type": "json_object" }
        )
        
        raw_json = response.choices[0].message.content
        
        # Pydantic will automatically validate the raw dictionary against GenerateResponse
        # If nodes or edges are missing/malformed, it throws a ValidationError
        parsed_data = json.loads(raw_json)
        return GenerateResponse(**parsed_data)