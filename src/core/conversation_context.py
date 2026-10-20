"""Resolve short follow-ups using a verified previous fact, never answer text."""
import re

from .college_scope import mentioned_colleges
from .college_topics import topics_for
from .question_understanding import needs_clarification
from .verified_college_answers import verified_fact_college, verified_fact_record


_LABELS = {
    'engineering': 'EGS Pillay Engineering College',
    'arts & science': 'EGS Pillay Arts and Science College',
    'polytechnic': 'EGS Pillay Polytechnic College',
    'pharmacy': 'EGS Pillay College of Pharmacy',
    'nursing': 'EGS Pillay College of Nursing',
    'education': 'EGS Pillay College of Education',
    'naturopathy': 'EGS Pillay Naturopathy and Yoga Medical College',
    'school': 'EGS Pillay International School',
}
_REFERENCES = re.compile(
    r'\b(?:it|its|they|their|them|those|that|this|same|there|adhu|athu|'
    r'adhoda|andha|idhu|inga|athula)\b', re.I,
)
_FOLLOWUP_START = re.compile(
    r'^(?:and\b|also\b|what about\b|how about\b|what is its\b|'
    r'how much\b|tell me more\b|more about\b|adhoda\b|'
    r'adhu\b|athu\b|andha\b|idhu\b|endha\b|eppo\b|'
    r'which (?:season|month|date)\b|when\b)', re.I,
)
_BARE_TOPIC = re.compile(
    r'^(?:the\s+)?(?:fees?|cost|duration|eligibility|admissions?|'
    r'placements?|scholarships?|courses?|departments?|scope|'
    r'hostel|transport|bus|timings?|intake|labs?|faculty|'
    r'infrastructure|cutoff|contact|results?|exams?)\??$', re.I,
)
_GROUP_OR_COMPARISON = re.compile(
    r'\b(?:all colleges|all institutions|group of institutions|'
    r'compare colleges|compare institutions)\b', re.I,
)


def contextualize_question(question: str, context_fact_id: str | None) -> str:
    """Add the prior college only for a clear, bounded follow-up.

    Explicitly named colleges and group-wide questions always win. Bare vague
    prompts retain their existing clarification/replay behavior.
    """
    if not context_fact_id or context_fact_id == 'group_institutions':
        return question
    if mentioned_colleges(question) or _GROUP_OR_COMPARISON.search(question):
        return question
    if needs_clarification(question):
        return question
    words = question.split()
    if len(words) > 14:
        return question
    if not (_REFERENCES.search(question) or _FOLLOWUP_START.search(question)
            or _BARE_TOPIC.fullmatch(question.strip()) or topics_for(question) and len(words) <= 5):
        return question
    college = verified_fact_college(context_fact_id)
    label = _LABELS.get(college or '')
    if not label:
        return question
    return f'{label}: {question}'


def contextual_follow_up_answer(question: str, context_fact_id: str | None) -> dict | None:
    """Handle bounded follow-ups without a noisy whole-corpus retrieval."""
    if not context_fact_id or mentioned_colleges(question):
        return None
    expanded = contextualize_question(question, context_fact_id)
    if expanded == question:
        return None
    fact = verified_fact_record(context_fact_id)
    if not fact:
        return None
    college = fact['college']
    label = _LABELS.get(college)
    if not label:
        return None
    lower = question.casefold()
    if context_fact_id in {
        'engineering_sports', 'engineering_extracurricular',
        'engineering_clubs_join', 'engineering_social_service',
    } and re.search(r'\b(?:when|month|season|date|eppo)\b', lower):
        timing = verified_fact_record('engineering_event_timing')
        if timing:
            return {
                'answer': timing['answer'],
                'source_url': timing['source_url'],
                'fact_id': timing['fact_id'],
            }
    if context_fact_id == 'engineering_transport' and re.search(r'\b(?:route|bus|timing|time|start)\b', lower):
        routes = [line for line in fact['answer'].splitlines() if re.match(r'^\d+\. ', line)]
        origin_matches = [line for line in routes
                          if re.search(re.escape(line.split(' — ', 1)[0].split('. ', 1)[1]), question, re.I)]
        if origin_matches:
            return {
                'answer': (
                    'Published EGSPEC transport route:\n- ' + '\n- '.join(origin_matches)
                    + '\n\nThis is the origin start time, not your stop pickup time. '
                    'Confirm the exact stop and current schedule with the Transport Department '
                    'at +91 75986 90315.'
                ),
                'source_url': fact['source_url'],
                'fact_id': context_fact_id,
            }
    if college == 'polytechnic' and re.search(r'\b(?:eligibility|eligible|qualification)\b', lower):
        admission = verified_fact_record('polytechnic_admission')
        if admission:
            return {
                'answer': admission['answer'],
                'source_url': admission['source_url'],
                'fact_id': admission['fact_id'],
            }
    if re.search(r'\b(?:courses?|programmes?|programs?|scope|careers?|duration)\b', lower):
        from .institution_guides import GUIDES
        overview_id = {
            'engineering': 'engineering_overview',
            'arts & science': 'arts_science_overview',
            'polytechnic': 'polytechnic_overview',
            'pharmacy': 'pharmacy_overview',
            'nursing': 'nursing_overview',
            'education': 'education_overview',
            'naturopathy': 'naturopathy_overview',
            'school': 'school_overview',
        }[college]
        overview = verified_fact_record(overview_id)
        if overview:
            return {
                'answer': GUIDES[overview_id],
                'source_url': overview['source_url'],
                'fact_id': overview_id,
            }
    if re.search(r'\b(?:hostel|facilities|infrastructure|labs?|library)\b', lower):
        facility_id = {
            'arts & science': 'arts_science_facilities',
            'polytechnic': 'polytechnic_facilities',
            'engineering': 'engineering_environment',
        }.get(college)
        facility = verified_fact_record(facility_id)
        if facility:
            return {
                'answer': facility['answer'],
                'source_url': facility['source_url'],
                'fact_id': facility_id,
            }
    if college != 'engineering' and re.search(r'\b(?:fees?|tuition|cost|eligibility|eligible|cutoff)\b', lower):
        detail = 'current fee amount' if re.search(r'\b(?:fees?|tuition|cost)\b', lower) else 'course-specific eligibility or cutoff'
        return {
            'answer': (
                f'For {label}, I cannot verify a {detail} from the current college-specific records. '
                'Tell me the exact course and admission year so I can narrow the answer; '
                'confirm the current notice with that college before applying.'
            ),
            'source_url': '',
            'fact_id': context_fact_id,
        }
    return None
