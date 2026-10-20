"""Resolve and enforce college ownership before assembling factual replies."""
import re
from urllib.parse import urlparse
from config import config

COLLEGES = {'engineering': ('engineering', 'egspec', 'பொறியியல்'), 'pharmacy': ('pharmacy', 'm.pharm', 'm pharm', 'b.pharm', 'b pharm', 'd.pharm', 'd pharm', 'pharm.d', 'pharm d', 'மருந்தியல்'), 'nursing': ('nursing', 'செவிலியர்'), 'polytechnic': ('polytechnic', 'பாலிடெக்னிக்'), 'school': ('matriculation', 'international school', 'school', 'பள்ளி'), 'arts & science': ('arts & science', 'arts and science', 'arts science', 'arts-science', 'arts college', 'கலை அறிவியல்'), 'education': ('college of education', 'education college', 'b.ed', 'b ed'), 'naturopathy': ('naturopathy', 'yoga medical college', 'bnys')}


def mentioned_colleges(text: str) -> set[str]:
    text = text.casefold()
    # "College and School of Nursing" identifies nursing, not another school.
    text = re.sub(r'(?:college and )?school of nursing', 'nursing', text)
    return {name for name, aliases in COLLEGES.items()
            if any(re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', text) for alias in aliases)}


def requested_colleges(query: str) -> set[str]:
    if re.search(r'\b(?:all|list|which)\s+(?:the\s+)?(?:colleges|institutions)\b.*\b(?:egs|pillay|group)\b|\b(?:egs|pillay)\b.*\b(?:all|list)\s+(?:the\s+)?(?:colleges|institutions)\b', query, re.I):
        return set(COLLEGES)
    explicit = mentioned_colleges(query)
    if explicit:
        return explicit
    if re.search(r'\b(?:all colleges|all institutions|group of institutions|list colleges|list institutions)\b', query, re.I):
        return set(COLLEGES)
    return mentioned_colleges(config.INSTITUTE_NAME) or {'engineering'}


def filter_college_evidence(query: str, evidence: list[dict], clean_lines) -> list[dict]:
    allowed = requested_colleges(query)
    filtered = []
    for item in evidence:
        source = f"{item.get('source', '')} {item.get('source_url', '')}"
        owners = mentioned_colleges(source)
        host = (urlparse(str(item.get('source_url', ''))).hostname or '').lower()
        if not owners and (host == 'egspec.org' or host.endswith('.egspec.org')):
            owners = {'engineering'}
        kept = []
        for line in clean_lines(str(item.get('text', ''))):
            explicit = mentioned_colleges(line)
            if explicit:
                owners = explicit
            elif re.search(r'\bgroup of institutions\b', line, re.I):
                owners = set(COLLEGES)
            # Reject mixed-college lines unless every college was requested.
            if owners and owners <= allowed:
                kept.append(line)
        if kept:
            filtered.append({**item, 'text': '\n'.join(kept)})
    return filtered
