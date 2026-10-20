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
    'engineering_sports': (
        'sports', 'college sports', 'sports available at egspec', 'sports and games',
        'football cricket basketball sports', 'sports quota and training',
        'college la sports enna iruku', 'sports facilities and achievements',
    ),
    'engineering_extracurricular': (
        'extracurricular activities', 'cultural events', 'fine arts club',
        'college cultural activities', 'extra curricular activities enna',
        'aksharam cultural event',
    ),
    'engineering_event_timing': (
        'events', 'when are sports and cultural events held', 'event season',
        'which month is sports day', 'aksharam date', 'event calendar',
        'endha season la events vaipanga', 'endha season la vaipanga',
        'sports fest eppo',
    ),
    'engineering_social_service': (
        'nss social service', 'red ribbon club activities', 'blood donation',
        'community service', 'volunteer opportunities',
        'social service la enna pannuvanga', 'nss activities',
    ),
    'engineering_collaborations': (
        'collaborations', 'who does egspec collaborate with', 'industry collaborations',
        'academic partners', 'college mou partners', 'collaboration organizations',
        'yaru kuda collaboration la irukanga', 'industry tie ups',
    ),
    'engineering_clubs_join': (
        'how to join college clubs', 'student clubs', 'club registration',
        'how to participate in extracurricular activities',
        'club la epadi join pannalam',
    ),
    'engineering_goal_theme': (
        'college main goal', 'what is the main goal of the college',
        'egspec focus', 'college theme', 'egspec theme', 'college motto',
        'what is the mission and theme', 'college oda main goal enna',
        'college oda theme enna',
    ),
    'engineering_environment': (
        'environment', 'college environment', 'campus environment',
        'what is the campus environment like', 'college atmosphere',
        'campus life environment', 'college oda environment epadi irukum',
    ),
    'engineering_vision_mission': (
        'vision and mission', 'college vision mission', 'egspec vision',
        'egspec mission', 'what is the vision and mission of the college',
        'college oda vison misson enna',
    ),
    'engineering_teaching': (
        'how do they teach', 'teaching methods', 'how does teaching work',
        'how are classes conducted', 'college la epadi teach pannuvanga',
        'practical teaching and internships', 'epadi tech pannu vanga',
    ),
    'engineering_po_co': (
        'po co', 'pos and cos', 'what are pos and cos', 'program outcomes',
        'programme outcomes', 'course outcomes', 'pso meaning',
        'co po mapping', 'egspec pos cos enna', 'pos and cos la enna',
    ),
    'engineering_placement_training': (
        'placement training', 'how are students trained for placements',
        'aptitude and soft skill training', 'placement ku epadi train pannuvanga',
        'interview training', 'placement ku la epadi train pannu vanga',
    ),
    'engineering_labs': (
        'lab facilities', 'college laboratories', 'computer labs',
        'how are the labs', 'laboratory facilities', 'lab facility epadi',
        'labs epadi irukum', 'lad fecility la epdi',
    ),
    'engineering_staff': (
        'staff details', 'how are the teachers', 'faculty and staff',
        'teachers qualification', 'staffs epadi', 'staffs la epdi', 'teaching faculty',
    ),
    'engineering_blocks': (
        'campus blocks', 'total blocks', 'block wise departments',
        'campus map', 'site map', 'sitemap',
        'which departments are in each block', 'campus block map',
        'main block gg block sj block', 'college site map blocks',
        'infrastructure site map', 'block la enna dept iruku',
        'total blocks enna indha block la enna dept iruku',
    ),
    'engineering_overview': (
        'tell me about egspec', 'tell me about egs pillay engineering college',
        'egspec overview', 'about egspec', 'engineering college overview',
        'egspec pathi sollu', 'ok tell me about egspec',
        'ok tell me about espec',
        'egspec',
        'ok tell me about egs pillay college', 'tell me about egs pillay college',
        'history', 'college history', 'egspec history',
    ),
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
    'engineering_admission_tnea': (
        'how can i join egspec through tnea and what cutoff is needed',
        'how to join egspec', 'egspec tnea admission', 'tnea cutoff',
        'minimum cutoff for egspec', 'maximum cutoff for egspec',
        'which department can i get for my cutoff', 'tnea code 3806',
        'engineering admission cutoff details',
        'engineering college la tnea moolama epadi join pandrathu cutoff fixed ah',
    ),
    'engineering_scholarships': (
        'what scholarships are available at egspec and who is eligible',
        'egspec scholarship details', 'scholarship eligibility',
        'merit scholarship', 'sigaram scholarship', 'scholarship',
    ),
    'engineering_transport': (
        'what are the egspec bus routes', 'egspec bus routes',
        'college bus route', 'transport routes', 'bus timing',
        'how does the college bus go', 'egspec college bus fee and pickup stop',
        'sirkali college bus route and timing',
        'mayiladuthurai college bus route and timing',
        'velankanni college bus route and timing',
        'who is the transport coordinator',
        'list egspec college bus routes and starting times',
    ),
    'engineering_student_count': (
        'how many students are there at egspec', 'total students',
        'student count', 'college student strength', 'number of students',
    ),
    'departments': (
        'departments', 'list all departments', 'what departments are available',
        'all ug and pg departments', 'college departments list',
        'engineering departments',
        'what are the courses', 'courses',
    ),
    'examinations': (
        'examinations', 'exam updates', 'exam timetable and results',
        'latest examination information',
    ),
    'latest_updates': (
        'latest updates', 'what are the latest egspec updates', 'latest college news',
        'recent egspec news and announcements',
    ),
    'placements': (
        'tell about the placement', 'tell me about placement', 'placement details',
        'give the placement details', 'give placement details',
        'highest placement', 'what is the highest placement',
        'placement record', 'placement recruiters',
        'give egspec placement details including package and recruiters',
        'placement package', 'lowest package', 'average package',
        'top companies hiring', 'how many students placed',
        'give full placement details highest lowest company salary and students placed',
        'highest lowest salary top companies and placed students',
        'give engineering placement highest package placement percentage recruiters and offers',
    ),
    'placement_2025_26_departments': (
        'what are the department wise placements for 2025 26',
        '2025 26 placement count', 'department wise placement statistics',
        'how many placements in each department', 'latest placement statistics',
    ),
    'academic_documents': (
        'where can i find egspec syllabus and academic regulations',
        'academic regulations', 'official syllabus', 'curriculum credits',
        'where to download syllabus', 'coe regulations',
    ),
    'central_admissions_contact': (
        'what are the egs pillay central admissions contacts',
        'admissions phone number', 'admission email', 'central admission office',
        'how can i contact admissions',
    ),
    'infrastructure': (
        'infrastructure', 'college infrastructure', 'campus infrastructure',
        'infrastructure details', 'college facilities and infrastructure',
        'give the infrastructure',
    ),
    'student_feedback': (
        'student feedback', 'give the student feedback', 'student reviews',
        'student opinion', 'student experience',
        'negative feedback about this college',
        'anything negative feedback about this college',
    ),
    'nba_programs_scope': (
        'which courses are nba accredited', 'nba courses', 'nba accredited programs',
        'what are the nba courses and their scope', 'which nba course has good scope',
        'nba course scope', 'list nba departments with career scope',
        'which is most deserving course in this college',
        'most deserving course in this college', 'best course in this college',
    ),
    'arts_science_overview': (
        'arts and science college la ug pg courses enna',
        'arts science college courses', 'arts and science departments',
        'arts science departments',
        'egs pillay arts science courses', 'arts science ug pg programs',
        'arts science research programs', 'arts science phd programs',
        'arts and science college courses',
        'what courses are in egs pillay arts and science college',
    ),
    'pharmacy_overview': (
        'pharmacy college la enna courses iruku', 'pharmacy courses enna',
        'pharmacy college courses', 'pharmacy college details',
        'd pharm b pharm pharm d m pharm details', 'pharmacy duration and intake',
        'pharmacy eligibility details', 'm pharm branches',
        'pharmacy course details',
        'pharmacy college courses enna',
        'explain d pharm b pharm pharm d m pharm duration intake branches and job scope',
    ),
    'nursing_overview': (
        'nursing college la enna courses iruku', 'nursing courses enna',
        'b sc nursing dgnm details', 'nursing college details',
        'nursing facilities and clinical training', 'is nursing inc recognized',
        'nursing placement assistance',
        'nursing college courses',
        'what nursing courses are available',
        'does nursing have inc recognition clinical training labs and placement assistance',
    ),
    'polytechnic_overview': (
        'polytechnic la enna diploma branches iruku', 'polytechnic branches',
        'polytechnic diploma courses enna', 'polytechnic college courses',
        'polytechnic aided and self financing branches',
        'polytechnic dote approval', 'diploma duration in polytechnic',
        'polytechnic diploma courses',
        'list polytechnic diploma branches',
        'tell me about egs pillay polytechnic diploma courses',
    ),
    'polytechnic_admission': (
        'polytechnic eligibility', 'diploma eligibility after 10th',
        'polytechnic lateral entry eligibility', 'diploma duration',
        'polytechnic admission documents', 'what certificates are needed for diploma',
        '10th 35 percent can i join polytechnic',
        'polytechnic join panna enna qualification',
        'diploma ku enna documents venum',
        'after 10th can i join polytechnic and what duration documents and percentage are needed',
    ),
    'polytechnic_facilities': (
        'polytechnic hostel bus lab facilities', 'polytechnic infrastructure',
        'does polytechnic have boys and girls hostel', 'polytechnic transport',
        'polytechnic facilities enna',
        'polytechnic la boys girls hostel bus wifi workshop la available',
    ),
    'polytechnic_admission_contact': (
        'polytechnic admission phone number', 'polytechnic admission email',
        'how to contact polytechnic', 'polytechnic admission contact',
    ),
    'arts_science_facilities': (
        'arts science infrastructure', 'arts science hostel library labs',
        'arts college facilities', 'arts science computer lab internet',
        'arts college la hostel library available',
        'arts and science college hostel library internet computer lab details',
    ),
    'arts_science_admission_contact': (
        'arts science admission phone number', 'arts science admission email',
        'how to contact arts college admissions', 'arts college admission contact',
        'arts college admission ku yaruku call pannanum mail enna',
    ),
    'pharmacy_admission_contact': (
        'pharmacy admission phone number', 'pharmacy admission email',
        'how to contact pharmacy admissions', 'pharmacy admission contact',
        'pharmacy admission ku contact number and mail',
    ),
    'nursing_admission_contact': (
        'nursing admission phone number', 'nursing admission email',
        'how to contact nursing admissions', 'nursing admission contact',
        'nursing join panna yaruku call pannanum eligibility age fee hum kekanum',
    ),
    'education_overview': (
        'college of education la enna course iruku', 'education college courses',
        'b ed course details', 'egs pillay education college details',
        'b ed availability in college of education',
        'education college subject combinations', 'b ed intake how much',
        'is b ed ncte approved which university is it affiliated to intake and college code',
        'education college b ed ku how many seat contact enna',
    ),
    'naturopathy_overview': (
        'naturopathy college course enna', 'naturopathy courses',
        'bnys course details', 'yoga medical college course',
        'bnys eligibility and duration', 'naturopathy approvals',
        'which course is offered by egs pillay naturopathy college',
        'explain bnys duration intake eligibility approval facilities and fees',
        'yoga medical college la enna course join panna mudiyum details',
    ),
    'school_overview': (
        'international school curriculum enna', 'international school details',
        'egs pillay school curriculum', 'school cbse details',
        'international school curriculum', 'international school class range',
        'school admission eligibility',
        'what curriculum class range fees and grade eligibility does the international school have',
        'international school cbse ah which class varaikum admission edukuranga',
    ),
    'group_institutions': (
        'which colleges are in egs pillay group', 'list all egs pillay institutions',
        'how many institutions are there', 'all colleges list',
        'egs group la enna colleges iruku',
        'list all colleges under egs pillay group',
    ),
    'engineering_chairperson': (
        'chair person', 'chairperson', 'college chairman', 'who is the chairperson',
        'who is the chairman', 'ok who is the chair person',
        'who is the egspec chairperson',
    ),
    'branch_aids': ('ai & ds', 'ai ds', 'aids', 'artificial intelligence and data science'),
    'branch_cse': ('cse', 'computer science and engineering'),
    'branch_it': ('it', 'information technology'),
    'branch_csbs': ('csbs', 'computer science and business systems'),
    'branch_bme': ('bme', 'biomedical engineering'),
    'branch_mechanical': ('mech', 'mechanical', 'mechanical engineering'),
    'branch_ece': ('ece', 'electronics and communication engineering'),
    'branch_eee': ('eee', 'electrical and electronics engineering'),
    'branch_civil': ('civil', 'civil engineering'),
    'branch_aiml': ('aiml', 'ai ml', 'artificial intelligence and machine learning'),
    'branch_cyber': ('cyber security', 'cybersecurity'),
}

_GREETINGS = {
    'hi', 'hello', 'hey', 'vanakkam', 'வணக்கம்',
    'good morning', 'good afternoon', 'good evening',
}
_THANKS = {
    'thanks', 'thank you', 'nandri', 'நன்றி', 'nice', 'good', 'ok nice',
    'okay nice', 'ok good', 'okay good', 'great', 'ok great',
    'super', 'ok super', 'okay super',
}
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
    college: str


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
    paths = [dataset_dir / filename for filename in ('train.jsonl', 'validation.jsonl')]
    paths.append(Path(config.BASE_DIR) / 'training' / 'campus-details-20261019' / 'train.jsonl')
    paths.append(Path(config.BASE_DIR) / 'training' / 'campus-details-20261019' / 'goal.jsonl')
    paths.append(Path(config.BASE_DIR) / 'training' / 'student-life-20261019' / 'train.jsonl')
    for path in paths:
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
            college = row.get('college', 'engineering').strip().casefold()
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
                'college': college,
            })
            if entry['source_url'] != source_url:
                raise ValueError(f'Conflicting verified sources for fact {fact_id!r}')
            if entry['college'] != college:
                raise ValueError(f'Conflicting college ownership for fact {fact_id!r}')
            entry['aliases'].append(question)
    for fact_id, aliases in _PHRASING_VARIANTS.items():
        if fact_id in facts:
            facts[fact_id]['aliases'].extend(aliases)
    from .institution_guides import BRANCH_SCOPE
    for fact_id, career_fields in BRANCH_SCOPE.items():
        if fact_id in facts:
            facts[fact_id]['answer'] += (
                f'\n\nTypical career fields: {career_fields}. '
                'These are possible paths, not guaranteed placements; specific jobs may require further skills or qualifications.'
            )
    return facts


def _find_fact(question: str, colleges: set[str]) -> tuple[VerifiedFact | None, float, bool]:
    normalized = _normalize_question(question)
    facts = _load_verified_answers()
    candidates = [fact for fact in facts.values() if fact['college'] in colleges]
    for fact in candidates:
        if normalized in {_normalize_question(alias) for alias in fact['aliases']}:
            return fact, 1.0, True

    # One or two content words are too ambiguous for fuzzy routing. Curated
    # exact aliases above still cover branch abbreviations and short topics.
    if len(_content_tokens(question)) <= 2:
        return None, 0.0, False

    scored = []
    for fact in candidates:
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
            'answer': 'Vanakkam! I can help with verified information about E.G.S. Pillay Engineering College. What would you like to know?',
            'source_url': '',
            'fact_id': '',
            'confidence': 1.0,
            'learnable': False,
        }
    if normalized in _THANKS:
        return {
            'answer': 'You’re welcome! What else would you like to know about the institution or course?',
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
    from .institution_guides import GUIDES
    colleges = requested_colleges(question)
    normalized = _normalize_question(question)
    if re.search(r'\barts\b', normalized) and not re.search(r'\bengineering\b', normalized):
        colleges = {'arts & science'}
    elif normalized in {'what is b ed', 'what is education'}:
        colleges = {'education'}
    elif normalized in {'what is paharmcy', 'what is pharamacy', 'what is pahaemacy'}:
        colleges = {'pharmacy'}
    # A subject/institution introduction needs a different answer from a
    # course-list or admission query, even when both share an overview fact.
    guide_colleges = {
        'engineering': 'engineering_overview',
        'arts & science': 'arts_science_overview',
        'pharmacy': 'pharmacy_overview',
        'nursing': 'nursing_overview',
        'polytechnic': 'polytechnic_overview',
        'education': 'education_overview',
        'naturopathy': 'naturopathy_overview',
        'school': 'school_overview',
    }
    broad_intent = bool(re.search(
        r'\b(?:overview|history|historical|chairman|chairperson|'
        r'tell me about|tell about|what about|explain|pathi sollu|scope|career fields)\b',
        normalized,
    )) or normalized in {
        'what is engineering', 'what is arts', 'what is arts and science',
        'what is pharmacy', 'what is nursing', 'what is polytechnic',
        'what is naturopathy', 'what is bnys', 'what is school',
        'what is b ed', 'what is education',
        'what is paharmcy', 'what is pharamacy', 'what is pahaemacy',
    }
    specific_intent = bool(re.search(
        r'\b(?:courses?|programs?|departments?|admission|fees?|eligibility|'
        r'placements?|intake|duration|cutoff|scholarships?)\b', normalized
    ))
    explicit_guide_target = bool(re.search(
        r'\b(?:egspec|espec|egs|pillay|engineering|arts|pharmacy|nursing|'
        r'polytechnic|naturopathy|school|education|bnys|paharmcy|pharamacy|pahaemacy)\b', normalized
    ))
    if len(colleges) == 1 and explicit_guide_target and broad_intent and not specific_intent:
        guide_id = guide_colleges[next(iter(colleges))]
        fact = _load_verified_answers().get(guide_id)
        if fact:
            return {
                'answer': GUIDES[guide_id],
                'source_url': fact['source_url'],
                'fact_id': guide_id,
                'confidence': 1.0,
                'learnable': False,
            }
    smalltalk = _smalltalk_result(question)
    if smalltalk:
        return {**smalltalk, 'confidence': 1.0, 'learnable': False}

    fact, confidence, exact_alias = _find_fact(question, colleges)
    if fact is not None and exact_alias:
        return {
            'answer': fact['answer'],
            'source_url': fact['source_url'],
            'fact_id': fact['fact_id'],
            'confidence': 1.0,
            'learnable': False,
        }

    if fact is None and context_fact_id and _is_follow_up(question):
        previous = _load_verified_answers().get(context_fact_id)
        if previous and (not colleges or previous['college'] in colleges or colleges == {'engineering'}):
            return {
                'answer': previous['answer'],
                'source_url': previous['source_url'],
                'fact_id': previous['fact_id'],
                'confidence': 0.9,
                'learnable': False,
            }

    # For the group institutions, only use curated exact intents here. A fuzzy
    # overview match must not swallow a specific fees, eligibility, ranking, or
    # accreditation question; those continue through grounded retrieval.
    if colleges != {'engineering'}:
        return None

    phrase = normalize_learnable_phrase(question)
    if phrase and len(_content_tokens(question)) > 2:
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


def verified_fact_college(fact_id: str | None) -> str | None:
    """Return a fact's verified owner without copying answer text into prompts."""
    fact = _load_verified_answers().get(fact_id or '')
    return fact['college'] if fact else None


def verified_fact_record(fact_id: str | None) -> VerifiedFact | None:
    """Return a curated fact for a bounded conversational follow-up."""
    return _load_verified_answers().get(fact_id or '')
