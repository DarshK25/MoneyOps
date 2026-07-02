from typing import Any, Dict


class MultiSourceSearch:
    def __init__(self):
        self.providers: Dict[str, Dict[str, Any]] = {}

    async def search(self, query: str, max_results: int = 5, **kwargs) -> Dict[str, Any]:
        if "duckduckgo" in self.providers and hasattr(self, "_search_duckduckgo"):
            return await self._search_duckduckgo(query, max_results=max_results)
        return {"results": [], "sources": []}