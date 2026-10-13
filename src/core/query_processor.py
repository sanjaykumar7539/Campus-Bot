"""Query analysis for institutional RAG.

Extracts lightweight intent and metadata hints without requiring an LLM.
This helps exact college terms (department, regulation, semester, year) survive retrieval.
"""
import re
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class QueryAnalysis:
    original: str
    normalized: str
    intent: str = 'general'
    metadata: Dict[str, str] = field(default_factory=dict)


class QueryProcessor:
    INTENTS = [
        ('fees', r'\b(fee|fees|tuition|payment|cost)\b'),
        ('exam', r'\b(exam|examination|test|timetable|schedule|result)\b'),
        ('admission', r'\b(admission|apply|application|eligibility|enroll|join)\b'),
        ('faculty', r'\b(faculty|staff|teacher|professor|hod)\b'),
        ('placement', r'\b(placement|recruit|company|job|career)\b'),
        ('hostel', r'\b(hostel|accommodation|mess|room)\b'),
        ('syllabus', r'\b(syllabus|subject|course|curriculum)\b'),
    ]

    DEPT_ALIASES = {
        'ai&ds': 'AI&DS', 'aids': 'AI&DS', 'artificial intelligence and data science': 'AI&DS',
        'cse': 'CSE', 'computer science': 'CSE', 'ece': 'ECE', 'eee': 'EEE',
        'mechanical': 'MECH', 'mech': 'MECH', 'civil': 'CIVIL', 'it': 'IT',
    }

    def analyze(self, query: str) -> QueryAnalysis:
        original = query or ''
        normalized = re.sub(r'\s+', ' ', original).strip()
        lowered = normalized.lower()
        intent = 'general'
        for name, pattern in self.INTENTS:
            if re.search(pattern, lowered):
                intent = name
                break

        metadata: Dict[str, str] = {}
        for alias, canonical in self.DEPT_ALIASES.items():
            if alias in lowered:
                metadata['department'] = canonical
                break

        reg = re.search(r'\b(?:regulation|reg)\s*[-:]?\s*(20\d{2})\b', lowered)
        if reg:
            metadata['regulation'] = reg.group(1)
        sem = re.search(r'\b(?:semester|sem)\s*[-:]?\s*([1-8])\b', lowered)
        if sem:
            metadata['semester'] = sem.group(1)
        year = re.search(r'\b(20\d{2})\b', lowered)
        if year:
            metadata.setdefault('year', year.group(1))
        return QueryAnalysis(original=original, normalized=normalized, intent=intent, metadata=metadata)
