from typing import Any, Dict, List


def _client_display_name(client: Dict[str, Any]) -> str:
    return client.get("name") or client.get("displayName") or client.get("display_name") or "Unknown Client"


class FinanceAgentCompat:
    def parse_line_items_text(self, text: str) -> List[Dict[str, Any]]:
        items = []
        for raw_line in (text or "").splitlines():
            parts = [p.strip() for p in raw_line.split("|")]
            if len(parts) < 4:
                continue
            item_type = (parts[0] or "SERVICE").upper()
            quantity = None if len(parts) > 2 and parts[2] in {"", "-"} else int(parts[2])
            rate = float(parts[3]) if parts[3] else 0.0
            gst = float(parts[4]) if len(parts) > 4 and parts[4] else 18.0
            items.append({
                "type": item_type,
                "description": parts[1],
                "quantity": quantity,
                "unit_price": rate,
                "gst_percent": gst,
            })
        return items


finance_agent = FinanceAgentCompat()