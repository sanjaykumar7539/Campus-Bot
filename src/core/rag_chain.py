"""Verified Q&A and structured answers from the indexed institute knowledge base."""
import re
from typing import Any, Dict
from urllib.parse import urlparse

from config import config
from .agentic_workflow import AgenticRAGWorkflow
from .guardrails import Guardrails
from .question_phrase_memory import get_question_phrase_memory
from .verified_college_answers import lookup_verified_answer
from .college_scope import COLLEGES, filter_college_evidence, requested_colleges
from .college_topics import TOPICS, topics_for, expand_question
from .question_understanding import normalize_question, needs_clarification, CLARIFICATION


_SECTION_RULES = (
    ('Institutions', re.compile(r'\b(group of institutions|college of|arts? & science|polytechnic|nursing|pharmacy)\b', re.I)),
    ('Courses & Departments', re.compile(r'\b(course|program|department|degree|b\.?e\.?|b\.?tech|b\.?sc|m\.?pharm|b\.?pharm|d\.?pharm|pharm\.?d|dgnm|diploma|mba|mca)\b', re.I)),
    ('Rankings & Accreditations', re.compile(r'\b(nirf|nba|naac|accredit|rank|tier|washington accord|ugc)\b', re.I)),
    ('Admissions & Fees', re.compile(r'\b(admission|apply|eligib|intake|fee|tuition|inr|rupee|contact|email|phone)\b|₹', re.I)),
)
_FEE_QUERY = re.compile(r'\b(fee|fees|tuition|cost|விடு|கட்டணம்)\b|₹', re.I)
_SPECIFIC_INSTITUTIONS = COLLEGES
_INSTITUTION_QUERIES = {
    'engineering': 'EGS Pillay Engineering College departments programmes courses accreditation ranking admissions',
    'pharmacy': 'EGS Pillay College of Pharmacy D.Pharm B.Pharm Pharm.D M.Pharm admissions',
    'nursing': 'EGS Pillay College and School of Nursing B.Sc Nursing DGNM admissions',
    'polytechnic': 'EGS Pillay Polytechnic College diploma DOTE programmes admissions',
    'school': 'EGS Pillay Matriculation School classes curriculum admissions',
    'arts & science': 'Edayathangudy G S Pillay Arts and Science College courses programmes admissions',
}
_GROUP_DIRECTORY_QUERY = (
    'EGS Pillay Group of Institutions colleges Engineering Arts Science Polytechnic '
    'Nursing Pharmacy Matriculation School programmes admissions NAAC NBA NIRF '
    'accreditation ranking'
)
_RANKING_TERMS = ('nba', 'nirf', 'naac')
_NOISE = re.compile(
    r'\b(copyright|all rights reserved|follow us|facebook|instagram|linkedin|'
    r'twitter|youtube|developed by|load more)\b',
    re.I,
)
_DYNAMIC_WEATHER = re.compile(
    r'\b(weather|overcast|sunny|cloudy|temperature|patchy rain)\b|'
    r'[-+]?\d+(?:\.\d+)?\s*°\s*c',
    re.I,
)
_METADATA_LINE = re.compile(r'^\s*(?:URL:|EXTRACTOR:|\[Institute:|\[Document|\[KAG Fact)', re.I)
_QUESTION_FRAGMENT = re.compile(
    r'^\s*(?:what|when|where|which|who|why|how|are|is|do|does|did|can|could|'
    r'would|should|may)\b', re.I,
)
_INCOMPLETE_ENDING = re.compile(
    r'\b(?:a|an|and|at|by|for|from|in|of|on|or|the|to|with)\s*$', re.I,
)
_BOILERPLATE = re.compile(
    r'\b(?:please (?:visit|refer to)|for more information|contact (?:the )?'
    r'admissions office|empower your future|secure your (?:future|spot)|'
    r'admissions? open|explore programs|follow us|on campus|for inquiries|'
    r'contact information|frequently asked questions|status page|sitemap|'
    r'privacy policy|terms & conditions|contact web admin|website last updated)\b', re.I,
)
_BARE_INSTITUTION = re.compile(
    r'^(?:(?:E\.?G\.?S\.?|Edayathangudy G S)\s+)?Pillay\s+'
    r'(?:(?:Engineering\s+)?College|Group of Institutions)\.?$', re.I,
)
_VAGUE_CLAIM = re.compile(
    r'\b(?:vary(?:ies)?(?: by program)?|offers? a range of online courses|'
    r'application processes?[^.]*vary)\b', re.I,
)
_QUERY_STOP_WORDS = {
    'a', 'an', 'and', 'are', 'at', 'can', 'could', 'did', 'do', 'does', 'for',
    'from', 'how', 'i', 'in', 'is', 'it', 'me', 'of', 'on', 'or', 'please',
    'tell', 'the', 'this', 'to', 'was', 'what', 'when', 'where', 'which',
    'who', 'why', 'with', 'would', 'you', 'your', 'about', 'all', 'details',
}
_QUERY_EQUIVALENTS = {
    'courses': 'program',
    'course': 'program',
    'programs': 'program',
    'departments': 'department',
    'fees': 'fee',
    'colleges': 'college',
    'institutions': 'institution',
}


class RAGChain:
    """Answer from verified facts first, then from trusted indexed institute documents."""

    def __init__(self, retriever: Any = None):
        self._retriever = retriever
        self.guardrails = Guardrails()
        self.workflow = AgenticRAGWorkflow(self._answer_from_retrieval)

    def _get_retriever(self):
        if self._retriever is None:
            from .retriever import Retriever
            self._retriever = Retriever()
        return self._retriever

    def warmup(self) -> dict:
        """Eagerly load retrieval models and the local corpus at app startup."""
        return self._get_retriever().warmup()

    @staticmethod
    def _retrieval_queries(query: str) -> list[str]:
        query_lower = query.casefold()
        queries = [query]
        selected = next(
            (
                name for name, aliases in _SPECIFIC_INSTITUTIONS.items()
                if any(alias in query_lower for alias in aliases)
            ),
            None,
        )
        if selected:
            topics = topics_for(query)
            if topics:
                terms = ' '.join(TOPICS[name][0] for name in TOPICS if name in topics)
                # invoke() normally expanded these terms already. Keep this
                # method useful for direct callers without duplicating search.
                if terms.casefold() not in query_lower:
                    queries.append(f'{selected} college {terms}')
            else:
                queries.append(_INSTITUTION_QUERIES.get(selected, query))
        if not selected and re.search(r'\b(all|list|each|group|institution|institutions|colleges|overview)\b', query_lower):
            queries.append(_GROUP_DIRECTORY_QUERY)
        return list(dict.fromkeys(queries))

    def _retrieve_bundle(self, query: str, k: int) -> dict:
        merged_evidence = {}
        merged_sources = {}
        for retrieval_query in self._retrieval_queries(query):
            bundle = self._get_retriever().retrieve_bundle(retrieval_query, k=k)
            for item in bundle.get('evidence', []):
                key = (item.get('source_url', ''), item.get('text', ''))
                current = merged_evidence.get(key)
                if current is None or float(item.get('score', 0.0)) > float(current.get('score', 0.0)):
                    merged_evidence[key] = item
            for item in bundle.get('sources', []):
                key = (
                    item.get('source_url', ''),
                    item.get('document', ''),
                    item.get('page', ''),
                )
                merged_sources[key] = item

        evidence = sorted(
            merged_evidence.values(),
            key=lambda item: float(item.get('score', 0.0)),
            reverse=True,
        )[:24]
        sources = list(merged_sources.values())
        return {
            'evidence': evidence,
            'sources': sources,
            'scores': [float(item.get('score', 0.0)) for item in evidence],
            'context': '\n\n'.join(str(item.get('text', '')) for item in evidence),
        }

    @staticmethod
    def _clean_evidence(text: str) -> list[str]:
        text = re.sub(r'\[Institute:[^\]]*\]', '', text)
        text = re.sub(r'https?://\S+', '', text)
        fragments = re.split(r'(?<=[.!?])\s+|\r?\n+', text)
        cleaned = []
        seen = set()
        for fragment in fragments:
            line = re.sub(r'\s+', ' ', fragment).strip(' \t-*•')
            if (
                not line
                or len(line) < 4
                or _METADATA_LINE.match(line)
                or _NOISE.search(line)
                or _DYNAMIC_WEATHER.search(line)
                or line.endswith('?')
                or _QUESTION_FRAGMENT.match(line)
                or _BOILERPLATE.search(line)
                or _BARE_INSTITUTION.match(line)
                or _VAGUE_CLAIM.search(line)
                or re.fullmatch(r'(?:FAQ`s|E\.?G\.?S\.?|\+?[\d\s().-]{8,})', line, re.I)
                or bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M', line, re.I))
                or _INCOMPLETE_ENDING.search(line)
                or line.startswith('/')
                or bool(re.match(r'^\+?[\d\s().-]{8,}\s+[A-Za-z]', line))
                or re.search(r'\bdoing business as\s*$', line, re.I)
            ):
                continue
            normalized = line.casefold()
            if normalized not in seen:
                cleaned.append(line[:360])
                seen.add(normalized)
        return cleaned

    @staticmethod
    def _subject_is_supported(query: str, evidence_text: str) -> bool:
        query_lower = query.casefold()
        evidence_lower = evidence_text.casefold()
        return all(
            not any(alias in query_lower for alias in aliases)
            or any(alias in evidence_lower for alias in aliases)
            for aliases in _SPECIFIC_INSTITUTIONS.values()
        )

    @staticmethod
    def _query_is_covered(query: str, evidence_text: str) -> bool:
        query_terms = {
            _QUERY_EQUIVALENTS.get(token, token)
            for token in re.findall(r'[a-z0-9]+', query.casefold())
            if token not in _QUERY_STOP_WORDS
        }
        evidence_terms = set(re.findall(r'[a-z0-9]+', evidence_text.casefold()))
        return bool(query_terms) and bool(query_terms & evidence_terms)

    @staticmethod
    def _trusted_url(url: str) -> bool:
        host = (urlparse(url).hostname or '').lower()
        return any(
            host == domain or host.endswith('.' + domain)
            for domain in config.NETWORK_ALLOWED_DOMAINS
        )

    @staticmethod
    def _requested_ranking_is_supported(query: str, evidence: list[dict]) -> bool:
        query_lower = query.casefold()
        subject_aliases = next(
            (
                aliases for aliases in _SPECIFIC_INSTITUTIONS.values()
                if any(alias in query_lower for alias in aliases)
            ),
            None,
        )
        requested_terms = [term for term in _RANKING_TERMS if term in query_lower]
        if re.search(r'\b(rank|ranking|accreditation|accredited)\b', query_lower) and not requested_terms:
            requested_terms = ['ranking or accreditation']
        for term in requested_terms:
            found = False
            for item in evidence:
                item_text = str(item.get('text', '')).casefold()
                source_context = (
                    f"{item.get('source', '')} {item.get('source_url', '')}"
                ).casefold()
                has_requested_fact = (
                    term in item_text
                    if term != 'ranking or accreditation'
                    else bool(re.search(r'\b(nirf|nba|naac|accredit|rank|tier)\b', item_text))
                )
                subject_supported = subject_aliases is None or any(
                    alias in item_text or alias in source_context
                    for alias in subject_aliases
                )
                if has_requested_fact and subject_supported:
                    found = True
                    break
            if not found:
                return False
        return True

    @staticmethod
    def _sections_for(line: str) -> list[str]:
        if _SECTION_RULES[2][1].search(line):
            return ['Rankings & Accreditations']
        sections = [title for title, pattern in _SECTION_RULES if pattern.search(line)]
        for name in topics_for(line):
            if name not in {'Admissions', 'Fees', 'Courses'}:
                sections.append(name)
        return list(dict.fromkeys(sections)) or ['Overview']

    def _format_structured_answer(self, query: str, evidence: list[dict]) -> str:
        sections: dict[str, list[str]] = {
            'Overview': [],
            'Institutions': [],
            'Courses & Departments': [],
            'Rankings & Accreditations': [],
            'Admissions & Fees': [],
        }
        sections.update({name: [] for name in TOPICS if name not in {'Admissions', 'Fees', 'Courses'}})
        requested_topics = topics_for(query) - {'Admissions', 'Fees', 'Courses'}
        query_lower = query.casefold()
        specific_subject_aliases = next(
            (
                aliases for aliases in _SPECIFIC_INSTITUTIONS.values()
                if any(alias in query_lower for alias in aliases)
            ),
            None,
        )
        group_overview = bool(
            re.search(r'\b(all|list|group|institutions|colleges|overview)\b', query_lower)
        )

        for item in evidence:
            text = str(item.get('text', ''))
            source_context = f"{item.get('source', '')} {item.get('source_url', '')}".casefold()
            item_topics = topics_for(f'{text} {source_context}')
            source_subject_matches = (
                any(alias in source_context for alias in specific_subject_aliases)
                if specific_subject_aliases
                else False
            )
            for line in self._clean_evidence(text):
                for section in self._sections_for(line):
                    if requested_topics and not ((topics_for(line) | item_topics) & requested_topics):
                        continue
                    if section == 'Overview' and group_overview:
                        continue
                    if (
                        group_overview
                        and section == 'Rankings & Accreditations'
                        and not re.search(
                            r'\b(group|institution|engineering|pharmacy|nursing|'
                            r'polytechnic|arts|science|school|college)\b',
                            line,
                            re.I,
                        )
                    ):
                        continue
                    requested_subject_matches = (
                        any(alias in line.casefold() for alias in specific_subject_aliases)
                        or source_subject_matches
                        if specific_subject_aliases
                        else True
                    )
                    if specific_subject_aliases and not requested_subject_matches:
                        continue
                    if (
                        specific_subject_aliases
                        and _SECTION_RULES[2][1].search(line)
                        and not requested_subject_matches
                    ):
                        continue
                    if (
                        specific_subject_aliases
                        and section == 'Admissions & Fees'
                        and re.search(r'\b(fee|fees|tuition|cost|inr|rupee)\b|₹', line, re.I)
                        and not requested_subject_matches
                    ):
                        continue
                    if line not in sections[section]:
                        sections[section].append(line)

        if _FEE_QUERY.search(query):
            fee_details = [
                line for line in sections['Admissions & Fees']
                if re.search(r'\b(fee|fees|tuition|cost)\b', line, re.I)
                and re.search(
                    r'(?:₹\s*[\d,]+|\bINR\s*[\d,]+|\b(?:Rs\.?|rupees?)\s*[\d,]+)',
                    line,
                    re.I,
                )
            ]
            if not fee_details:
                phone_number = re.compile(r'(?<!\w)\+?\d[\d\s().-]{8,}\d(?!\w)')
                for title, facts in sections.items():
                    if title != 'Admissions & Fees':
                        sections[title] = [
                            phone_number.sub('', fact).strip(' :-,')
                            for fact in facts
                        ]
                        sections[title] = [fact for fact in sections[title] if fact]
                if not re.search(
                    r'\b(program|programs|course|courses|department|departments|'
                    r'accreditation|ranking|rankings|institution|institutions)\b',
                    query,
                    re.I,
                ):
                    for title in sections:
                        if title != 'Admissions & Fees':
                            sections[title] = []
                sections['Admissions & Fees'] = []
                sections['Admissions & Fees'].append(
                    'I could not verify a current fee amount in the official information available to me. '
                    f'Please contact admissions for the latest fee schedule: {config.ADMISSIONS_CONTACT_URL}'
                )

        # Keep replies readable while avoiding an unsupported long-form summary.
        output = []
        remaining = 2200
        for title, facts in sections.items():
            if not facts:
                continue
            heading = f'{title}\n'
            body = '\n'.join(f'- {fact}' for fact in facts[:5])
            block = f'{heading}{body}'
            if len(block) > remaining:
                block = block[:max(0, remaining - 1)].rsplit('\n', 1)[0]
            if block:
                output.append(block)
                remaining -= len(block) + 2
            if remaining <= 0:
                break
        return '\n\n'.join(output)

    def _answer_from_retrieval(self, query: str, retrieval_k: int | None = None) -> Dict:
        bundle = self._retrieve_bundle(query, retrieval_k or 8)
        evidence = [
            item for item in bundle.get('evidence', [])
            if self._trusted_url(str(item.get('source_url', '')))
        ]
        evidence = filter_college_evidence(query, evidence, self._clean_evidence)
        trusted_urls = {
            str(item.get('source_url', ''))
            for item in evidence
        }
        sources = [
            item for item in bundle.get('sources', [])
            if str(item.get('source_url', '')) in trusted_urls
        ]
        clean_lines = [
            line
            for item in evidence
            for line in self._clean_evidence(str(item.get('text', '')))
        ]
        context = '\n'.join(clean_lines)
        scores = [float(item.get('score', 0.0)) for item in evidence]
        grounding = self.guardrails.check_grounding(context, query, scores)

        if (
            not grounding['is_grounded']
            or not self._query_is_covered(query, context)
            or not sources
            or not self._subject_is_supported(
                query,
                '\n'.join(str(item.get('text', '')) for item in evidence),
            )
            or not self._requested_ranking_is_supported(query, evidence)
        ):
            return {
                'answer': config.FALLBACK_MESSAGE,
                'sources': [],
                'confidence': 0.0,
                'is_grounded': False,
                'reason': grounding['reason'],
            }

        answer = self._format_structured_answer(query, evidence)
        if not answer:
            return {
                'answer': config.FALLBACK_MESSAGE,
                'sources': [],
                'confidence': 0.0,
                'is_grounded': False,
                'reason': 'Retrieved records did not contain a readable answer',
            }
        return {
            'answer': answer,
            'sources': sources,
            'confidence': float(grounding['score']),
            'is_grounded': True,
            'reason': 'Structured answer assembled from retrieved institute records',
        }

    def invoke(self, query: str, context_fact_id: str | None = None) -> Dict:
        query = normalize_question(query)
        if needs_clarification(query):
            if context_fact_id:
                query = 'what about that?'
            else:
                return {'answer': CLARIFICATION, 'sources': [], 'confidence': 0.0,
                        'is_grounded': False, 'reason': 'Clarification needed'}
        verified = (lookup_verified_answer(query, context_fact_id=context_fact_id)
                    if requested_colleges(query) == {'engineering'} else None)
        if verified is not None:
            fact_id = str(verified.get('fact_id', ''))
            if fact_id and verified.get('learnable'):
                get_question_phrase_memory().remember(query, fact_id)
            return {
                'answer': str(verified['answer']),
                'sources': [{
                    'document': str(verified['source_url']),
                    'page': 'verified college Q&A',
                    'relevance_score': 1.0,
                }] if verified['source_url'] else [],
                'confidence': float(verified['confidence']),
                'is_grounded': True,
                'reason': 'Matched a verified institute answer',
                'fact_id': fact_id,
            }

        if needs_clarification(query):
            return {'answer': CLARIFICATION, 'sources': [], 'confidence': 0.0,
                    'is_grounded': False, 'reason': 'Clarification needed'}
        return self.workflow.invoke(query=expand_question(query), retry_retrieval_k=12)
