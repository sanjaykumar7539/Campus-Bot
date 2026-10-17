"""Conservative local normalization; preserve numbers and requested college."""
import re

_PHRASES = {
    'start pannanga': 'established', 'start pannadhu': 'established',
    'aarambicha varusham': 'established year', 'full peru': 'full name',
    'vela vaippu': 'placement', 'velai vaaippu': 'placement',
    'evvalavu fees': 'how much fees', 'how much will i have to pay': 'fees',
    'how much would i need to pay': 'fees', 'how do i get into': 'admission eligibility',
    'companies come for recruitment': 'placement recruiters',
    'stay on campus': 'hostel accommodation', 'where can i stay': 'hostel accommodation',
    'when did it open': 'when was the college established',
}
_WORDS = {
    'engg': 'engineering', 'enginering': 'engineering', 'engineeringg': 'engineering',
    'pharamcy': 'pharmacy', 'nursng': 'nursing', 'hostal': 'hostel',
    'placment': 'placement', 'scholorship': 'scholarship', 'admisson': 'admission',
    'eppo': 'when', 'aarambichanga': 'established', 'aarambichathu': 'established',
    'varusham': 'year', 'ethana': 'how many', 'evlo': 'how much',
    'kattanam': 'fees', 'kattanan': 'fees', 'peru': 'name',
    'iruka': 'available', 'irukka': 'available', 'sollunga': '', 'sollu': '',
}
_VAGUE = {'details', 'more details', 'tell me more', 'explain it', 'what about it',
          'adhu', 'athu', 'enna details', 'puriyala', 'idhu', 'that', 'this'}

def normalize_question(query):
    text = re.sub(r'\s+', ' ', query or '').strip()
    for phrase, replacement in sorted(_PHRASES.items(), key=lambda item: -len(item[0])):
        text = re.sub(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', replacement, text, flags=re.I)
    text = re.sub(r'[a-zA-Z]+', lambda match: _WORDS.get(match.group().casefold(), match.group()), text)
    return re.sub(r'\s+', ' ', text).strip()

def needs_clarification(query):
    text = re.sub(r'[^\w\s]', '', query.casefold())
    return ' '.join(text.split()) in _VAGUE

CLARIFICATION = (
    'Which college and which detail would you like to know? '
    'For example: engineering fees, nursing hostel, or pharmacy admissions. '
    'Please include the department or year if relevant.'
)
