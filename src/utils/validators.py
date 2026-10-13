import re
from typing import Tuple

def validate_query(query: str) -> Tuple[bool, str]:
    if not query or not query.strip():
        return False, "Query cannot be empty"
    if len(query) > 1000:
        return False, "Query too long (max 1000 characters)"
    harmful_patterns = [
        r"<script", r"javascript:", r"on\w+\s*=",
        r"DROP\s+TABLE", r"DELETE\s+FROM",
    ]
    for pattern in harmful_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False, "Invalid query format"
    return True, "Valid"
