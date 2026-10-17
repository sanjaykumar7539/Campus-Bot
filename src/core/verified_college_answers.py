"""Verified institute answers with conservative natural-phrasing matching."""
from difflib import SequenceMatcher
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

from config import config
from .question_phrase_memory import normalize_learnable_phrase


def _normalize_question(question: str) -> str:
    return ' '.join(re.sub(r'[^\w]+', ' ', question.casefold(), flags=re.UNICODE).split())


_FILLER_WORDS = {
    'a', 'an', 'and', 'are', 'can', 'could', 'did', 'do', 'does', 'for', 'give',
    'hey', 'hi', 'i', 'is', 'it', 'kindly', 'me', 'of', 'please', 'tell', 'the',
    'there', 'this', 'to', 'was', 'were', 'would', 'you', 'your', 'about',
    'information', 'know', 'need', 'want', 'oda', 'la',
}

_TOKEN_EQUIVALENTS = {
    'began': 'established', 'begin': 'established', 'founded': 'established',
    'opened': 'established', 'started': 'established', 'start': 'established',
    'formed': 'established', 'launched': 'established', 'peru': 'name',
    'fullname': 'name', 'full': 'name', 'form': 'name', 'meaning': 'name',
    'means': 'name', 'stand': 'name',
    'stands': 'name', 'course': 'program', 'courses': 'program',
    'programme': 'program', 'programmes': 'program', 'degrees': 'program',
    'degree': 'program', 'trust': 'trust', 'university': 'university',
    'eppo': 'when', 'yaaru': 'who', 'yaru': 'who', 'enna': 'what',
}

_PHRASING_VARIANTS = {
    'college_name': (
        'what does egspec stand for', 'egs full form enna', 'egspec meaning',
        'college peru enna', 'college oda name enna', 'egs pillay college name',
        'egspec என்றால் என்ன', 'கல்லூரியின் முழு பெயர் என்ன',
    ),
    'established': (
        'when was the college founded', 'when did egspec start', 'college started year',
        'college eppo start aachu', 'college aarambicha year enna',
        'கல்லூரி எப்போது தொடங்கப்பட்டது', 'கல்லூரி தொடங்கிய ஆண்டு என்ன',
    ),
    'founder': (
        'who founded egspec', 'who started the college', 'which trust started college',
        'college start pannadhu yaaru', 'college ah aarambichadhu yaaru',
        'கல்லூரியை நிறுவிய அறக்கட்டளை எது',
    ),
    'initial_courses': (
        'what courses were offered first', 'which programs did the college start with',
        'first subjects in college', 'college first courses enna',
        'முதலில் என்ன பாடப்பிரிவுகள் இருந்தன',
    ),
    'anna_affiliation': (
        'which university is the college affiliated with', 'anna university affiliation year',
        'college endha university affiliated', 'எந்த பல்கலைக்கழகத்துடன் இணைக்கப்பட்டது',
    ),
    'ugc': (
        'ugc recognition details', 'is the college ugc recognized', 'ugc 2f 12b status',
        'யுஜிசி அங்கீகாரம் உள்ளதா',
    ),
    'autonomous': (
        'when did the college become autonomous', 'autonomous status from which year',
        'college autonomous eppo aachu', 'தன்னாட்சி அந்தஸ்து எப்போது கிடைத்தது',
    ),
    'program_counts': (
        'how many ug and pg programs', 'number of undergraduate postgraduate courses',
        'college la ethana ug pg programs irukku', 'மொத்தம் எத்தனை இளநிலை முதுநிலை படிப்புகள்',
    ),
    'research_centers': (
        'which departments offer phd research', 'recognized research center departments',
        'phd research endha departments la irukku', 'ஆராய்ச்சி மையம் உள்ள துறைகள் எவை',
    ),
    'qic': (
        'what is the qic nodal center', 'quality improvement cell anna university',
        'கியூஐசி நோடல் மையம்',
    ),
    'iirs': (
        'what is the college iirs role', 'iirs outreach program nodal center',
        'ஐஐஆர்எஸ் திட்டத்தில் கல்லூரியின் பங்கு',
    ),
    'nirf_2025': (
        'what is the college nirf rank', 'nirf ranking band 2025', 'college nirf placement',
        'நிர்ஃப் 2025 தரவரிசை',
    ),
    'admissions': (
        'what programs are available for admission', 'admission subjects and degree levels',
        'admission la enna courses irukku', 'சேர்க்கைக்கு என்ன படிப்புகள் உள்ளன',
    ),
    'departments': (
        'departments', 'list all departments', 'what departments are available',
        'all ug and pg departments', 'college departments list',
    ),
    'examinations': (
        'examinations', 'exam updates', 'exam timetable and results',
        'latest examination information',
    ),
    'latest_updates': (
        'latest updates', 'what are the latest egspec updates', 'latest college news',
        'recent egspec news and announcements',
    ),
}

_GREETINGS = {
    'hi', 'hello', 'hey', 'vanakkam', 'வணக்கம்',
    'good morning', 'good afternoon', 'good evening',
}
_THANKS = {'thanks', 'thank you', 'nandri', 'நன்றி'}
_FOLLOW_UP_TOKENS = {
    'it', 'its', 'that', 'this', 'they', 'them', 'their', 'there', 'those',
    'same', 'adhu', 'athu', 'anga', 'அது', 'அதில்', 'இது', 'இதில்', 'அவை',
}
_FOLLOW_UP_STARTERS = {'and', 'then', 'so', 'what', 'when', 'where', 'who', 'which', 'how', 'is', 'are', 'was', 'were'}
_QUESTION_INTENTS = {'when', 'who', 'what', 'which', 'where', 'how'}


class VerifiedFact(TypedDict):
    fact_id: str
    answer: str
    source_url: str
    aliases: list[str]


class VerifiedMatch(TypedDict):
    answer: str
    source_url: str
    fact_id: str
    confidence: float
    learnable: bool


def _content_tokens(question: str) -> set[str]:
    tokens = _normalize_question(question).split()
    content = []
    for token in tokens:
        if token in _FILLER_WORDS:
            continue
        token = _TOKEN_EQUIVALENTS.get(token, token)
        if len(token) > 3 and token.endswith('s') and token not in {'is'}:
            token = token[:-1]
        content.append(token)
    return set(content)


def _similarity(question: str, alias: str) -> float:
    query_tokens = _content_tokens(question)
    alias_tokens = _content_tokens(alias)
    if not query_tokens or not alias_tokens:
        return 0.0
    overlap = len(query_tokens & alias_tokens)
    coverage = overlap / len(query_tokens)
    specificity = overlap / len(alias_tokens)
    token_score = (0.8 * coverage) + (0.2 * specificity)
    query_intents = query_tokens & _QUESTION_INTENTS
    alias_intents = alias_tokens & _QUESTION_INTENTS
    if query_intents and alias_intents and query_intents.isdisjoint(alias_intents):
        return token_score
    query_text = ' '.join(sorted(query_tokens))
    alias_text = ' '.join(sorted(alias_tokens))
    string_score = SequenceMatcher(None, query_text, alias_text).ratio()
    return max(token_score, string_score)


@lru_cache(maxsize=1)
def _load_verified_answers() -> dict[str, VerifiedFact]:
    dataset_dir = Path(config.BASE_DIR) / 'training' / 'online-college-qa'
    facts: dict[str, VerifiedFact] = {}
    for filename in ('train.jsonl', 'validation.jsonl'):
        path = dataset_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f'College answer verification dataset is missing: {path}')
        for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            question = row.get('question', '').strip()
            answer = row.get('answer', '').strip()
            source_url = row.get('source_url', '').strip()
            fact_id = row.get('fact_id', '').strip()
            host = (urlparse(source_url).hostname or '').lower()
            trusted_source = any(
                host == domain or host.endswith('.' + domain)
                for domain in config.NETWORK_ALLOWED_DOMAINS
            )
            if not question or not answer or not fact_id or not trusted_source:
                raise ValueError(f'Invalid verified college Q&A at {path}:{line_number}')
            entry = facts.setdefault(fact_id, {
                'fact_id': fact_id,
                'answer': answer,
                'source_url': source_url,
                'aliases': [],
            })
            if entry['source_url'] != source_url:
                raise ValueError(f'Conflicting verified sources for fact {fact_id!r}')
            entry['aliases'].append(question)
    for fact_id, aliases in _PHRASING_VARIANTS.items():
        if fact_id in facts:
            facts[fact_id]['aliases'].extend(aliases)
    return facts


def _find_fact(question: str) -> tuple[VerifiedFact | None, float, bool]:
    normalized = _normalize_question(question)
    facts = _load_verified_answers()
    for fact in facts.values():
        if normalized in {_normalize_question(alias) for alias in fact['aliases']}:
            return fact, 1.0, True

    scored = []
    for fact in facts.values():
        aliases = fact['aliases']
        score = max((_similarity(question, alias) for alias in aliases), default=0.0)
        scored.append((score, fact))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored or scored[0][0] < 0.72:
        return None, scored[0][0] if scored else 0.0, False
    if len(scored) > 1 and scored[0][0] - scored[1][0] < 0.12:
        return None, scored[0][0], False
    return scored[0][1], scored[0][0], False


def _smalltalk_result(question: str) -> VerifiedMatch | None:
    normalized = _normalize_question(question)
    if normalized in _GREETINGS:
        return {
            'answer': 'Vanakkam! I can help with verified information about E. G. S. Pillay Engineering College. What would you like to know?',
            'source_url': '',
            'fact_id': '',
            'confidence': 1.0,
            'learnable': False,
        }
    if normalized in _THANKS:
        return {
            'answer': 'You’re welcome! Feel free to ask about E. G. S. Pillay Engineering College.',
            'source_url': '',
            'fact_id': '',
            'confidence': 1.0,
            'learnable': False,
        }
    return None


def _is_follow_up(question: str) -> bool:
    words = _normalize_question(question).split()
    return (
        len(words) <= 7
        and bool(set(words) & _FOLLOW_UP_TOKENS)
        and bool(words)
        and words[0] in _FOLLOW_UP_STARTERS
        and set(words) <= (_FOLLOW_UP_TOKENS | _FOLLOW_UP_STARTERS | {'many', 'much', 'more', 'about', 'explain', 'tell', 'me', 'please', 'detail', 'details', 'of', 'the'})
    )


def lookup_verified_answer(
    question: str,
    context_fact_id: str | None = None,
) -> VerifiedMatch | None:
    """Find a unique high-confidence verified fact from a natural phrasing."""
    if not question or not question.strip():
        return None
    from .college_scope import requested_colleges
    if requested_colleges(question) != {'engineering'}:
        return None
    smalltalk = _smalltalk_result(question)
    if smalltalk:
        return {**smalltalk, 'confidence': 1.0, 'learnable': False}

    fact, confidence, exact_alias = _find_fact(question)
    if fact is not None and exact_alias:
        return {
            'answer': fact['answer'],
            'source_url': fact['source_url'],
            'fact_id': fact['fact_id'],
            'confidence': 1.0,
            'learnable': False,
        }

    phrase = normalize_learnable_phrase(question)
    if phrase:
        from .question_phrase_memory import get_question_phrase_memory
        learned_fact_id = get_question_phrase_memory().get_fact_id(phrase)
        if learned_fact_id:
            fact = _load_verified_answers().get(learned_fact_id)
            if fact:
                return {
                    'answer': fact['answer'],
                    'source_url': fact['source_url'],
                    'fact_id': fact['fact_id'],
                    'confidence': 1.0,
                    'learnable': False,
                }

    if fact is None:
        if context_fact_id and _is_follow_up(question):
            fact = _load_verified_answers().get(context_fact_id)
            if fact:
                return {
                    'answer': fact['answer'],
                    'source_url': fact['source_url'],
                    'fact_id': fact['fact_id'],
                    'confidence': 0.9,
                    'learnable': False,
                }
        return None
    return {
        'answer': fact['answer'],
        'source_url': fact['source_url'],
        'fact_id': fact['fact_id'],
        'confidence': confidence,
        'learnable': not exact_alias and confidence >= 0.78 and phrase is not None,
    }


def verified_answers_available() -> bool:
    return bool(_load_verified_answers())
