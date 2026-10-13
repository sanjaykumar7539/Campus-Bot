import html
import re
from typing import List, Dict


class ResponseFormatter:
    def format(self, answer: str, sources: List[Dict]) -> str:
        formatted = answer
        if sources:
            formatted += '\n\nSources:'
            seen = set()
            for src in sources:
                doc = src.get('document', 'Unknown')
                if doc not in seen:
                    seen.add(doc)
                    formatted += f"\n- {doc} (Page {src.get('page', 'N/A')})"
        return formatted

    def to_html(self, text: str) -> str:
        # Escape first, then allow our tiny markdown subset.
        safe = html.escape(text or '')
        safe = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', safe)
        return f'<div class="bot-message">{safe.replace(chr(10), "<br>")}</div>'
