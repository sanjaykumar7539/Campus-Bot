from typing import List, Dict


class ContextWindow:
    def __init__(self, max_tokens: int = 2048, max_messages: int = 6):
        self.max_tokens = max_tokens
        self.max_messages = max_messages

    def build_context(self, messages: List[Dict]) -> str:
        recent = messages[-self.max_messages:]
        selected = []
        used = 0
        for msg in reversed(recent):
            role = 'User' if msg.get('role') == 'user' else 'Assistant'
            line = f"{role}: {msg.get('content', '')}"
            cost = self.estimate_tokens(line)
            if selected and used + cost > self.max_tokens:
                break
            selected.append(line)
            used += cost
        return '\n'.join(reversed(selected))

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text or '') // 4)
