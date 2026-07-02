import json
import re
from typing import Any, Dict, List, Optional


class GroqClientCompat:
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ):
        raise RuntimeError("groq_client.chat_completion must be mocked in tests or configured by the caller")

    async def simple_completion(self, prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        response = await self.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def chat_completion_with_json(self, messages: List[Dict[str, str]], temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        response = await self.chat_completion(messages=messages, temperature=temperature, max_tokens=max_tokens)
        content = response.choices[0].message.content.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            content = match.group(1)
        return json.loads(content)


groq_client = GroqClientCompat()