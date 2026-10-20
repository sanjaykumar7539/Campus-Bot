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
    'espec': 'egspec', 'tel': 'tell', 'abot': 'about',
    'pharamcy': 'pharmacy', 'parmachy': 'pharmacy', 'parmacy': 'pharmacy',
    'pharmcy': 'pharmacy', 'nurshibg': 'nursing', 'nursibg': 'nursing',
    'nursng': 'nursing', 'polytecnic': 'polytechnic',
    'politechnic': 'polytechnic', 'hostal': 'hostel',
    'placment': 'placement', 'scholorship': 'scholarship', 'admisson': 'admission',
    'admision': 'admission', 'nurshing': 'nursing', 'clg': 'college',
    'numbr': 'number', 'schol': 'school',
    'colege': 'college', 'cahir': 'chair', 'persaon': 'person',
    'somwthig': 'something', 'somthing': 'something', 'somethig': 'something',
    'placemant': 'placement', 'placemetn': 'placement', 'detials': 'details',
    'detial': 'detail', 'gieve': 'give', 'givee': 'give', 'collage': 'college',
    'enviroment': 'environment', 'envirnment': 'environment',
    'infrastucture': 'infrastructure', 'infrastrcture': 'infrastructure',
    'departmant': 'department', 'corses': 'courses', 'eligiblity': 'eligibility',
    'acriditation': 'accreditation', 'pharmasy': 'pharmacy',
    'scince': 'science',
    'tomorow': 'tomorrow', 'availble': 'available', 'studnts': 'students',
    'certficate': 'certificate', 'libary': 'library',
    'examnation': 'examination', 'sylabus': 'syllabus', 'teh': 'the',
    'plese': 'please',
    'eppo': 'when', 'aarambichanga': 'established', 'aarambichathu': 'established',
    'varusham': 'year', 'ethana': 'how many', 'evlo': 'how much',
    'kattanam': 'fees', 'kattanan': 'fees', 'peru': 'name',
    'iruka': 'available', 'irukka': 'available', 'sollunga': '', 'sollu': '',
}
_VAGUE = {'details', 'more details', 'tell me more', 'explain it', 'what about it',
          'adhu', 'athu', 'enna details', 'puriyala', 'idhu', 'that', 'this',
          'anything special', 'any thing special', 'what is special',
          'give the environment', 'environment', 'tell about something',
          'tell me something', 'something'}

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
