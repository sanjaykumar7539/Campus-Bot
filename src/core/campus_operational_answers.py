"""Fast, conservative responses for operational campus questions.

These questions commonly ask about relative dates, staff availability, room
locations, forms, or lab material.  When no live official record is attached,
the assistant must say exactly what is unverified and give the useful next step
instead of redirecting every question to Admissions.
"""
import re

from src.utils.translator import detect_language


_EVENT = re.compile(
    r'\b(?:model exams?|semester exams?|project expo|sports day|alumni meet|'
    r'symposium|guest lecture|cultural fest|hackathon|annual day|workshop|'
    r'placement drive)\b', re.I,
)
_FACILITY = re.compile(
    r'\b(?:central library|digital library|girls hostel|boys hostel|main canteen|'
    r'station(?:e|a)ry shop|auditorium|seminar hall|admin office|placement cell|'
    r'medical room|sports ground|gym)\b', re.I,
)
_PERSON = re.compile(
    r'\b(?:hod|class advisor|principal|librarian|warden|placement officer|'
    r'lab assistant|security guard)\b', re.I,
)
_DOCUMENT = re.compile(
    r'\b(?:no[- ]?due form|bus pass|hall ticket|medical certificate|bonafide '
    r'certificate|outpass|duplicate|scholarship form|fees receipt|id card|'
    r'first graduate certificate|transfer certificate)\b', re.I,
)
_LAB = re.compile(r'\b(?:lab manual|lab(?:oratory)?|software|syllabus)\b', re.I)
_ACADEMIC_RULE = re.compile(
    r'\bhow many credits?\b.*\b(?:paper|subject|course)\b', re.I,
)
_OPERATIONAL = re.compile(
    r'\b(?:today|tomorrow|naalaiku|morning|afternoon|evening|next week|'
    r'next month|eppo|where|enga|timing|what time|open|close|available|'
    r'allow|attend|meet|contact|located|vaanga|kedaikkum|irukka)\b', re.I,
)


def _subject(pattern: re.Pattern, question: str, fallback: str) -> str:
    match = pattern.search(question)
    return match.group(0) if match else fallback


def _localized(answer: str, fact_id: str, question: str, subject: str = '') -> str:
    language = detect_language(question)
    if language == 'tanglish':
        replies = {
            'operational_event': (
                f'Ketta event: {subject}.\n'
                'Current status: Indha exact department/date-ku verified live dated notice indexed records-la illa.\n'
                'Enga check pannanum: Department event-na department notice/class group; exam-na COE portal; placement drive-na Placement Cell.\n'
                'Confirm pannunga: Date, reporting time, venue, eligibility, ID or hall ticket.\n'
                'Mukkiyam: Today, tomorrow, next week madhiri query-ku dated live notice thevai.'
            ),
            'operational_facility': (
                f'Ketta facility: {subject}.\n'
                'Current status: Exact live opening time, closing time or block location verified records-la illa.\n'
                'Enga confirm pannanum: Campus directory/security desk; library timing-ku Library desk; hostel-ku Hostel office; gym/sports-ku Physical Education department.\n'
                'Mukkiyam: Holiday, exam day and special event day-la timing maaralam.'
            ),
            'operational_person': (
                f'Ketta staff: {subject}.\n'
                'Availability: Live duty schedule or room status official indexed records-la publish pannala.\n'
                'Best option: Visit panna munadi relevant department office-la confirm pannunga; Principal-ku Administrative Office, hostel-ku Warden, placement-ku Placement Cell.\n'
                'Share pannunga: Name, register number, department, purpose and preferred meeting time.'
            ),
            'operational_document': (
                f'Ketta document: {subject}.\n'
                'Current status: Indha request-oda exact issue time, fee or approval rule verified records-la illa.\n'
                'Enga start pannanum: Department office/Class Advisor; exam document-na Controller of Examinations (COE); hostel outpass-na Warden; bus pass-na Transport department.\n'
                'Kondu ponga: Student ID and request-ku relevant supporting proof.\n'
                'Mukkiyam: Current notice illama unofficial deadline or fee-ai nambatheenga.'
            ),
            'operational_lab': (
                f'Ketta academic item: {subject}.\n'
                'Current status: Exact manual, syllabus version or software list verified records-la illa.\n'
                'Enga kedaikkum: department LMS/office-la check panni subject faculty or lab in-charge kitta confirm pannunga.\n'
                'Confirm pannunga: Regulation year, semester, department and academic year.'
            ),
            'operational_academic_rule': (
                'Ketta detail: Course credit information.\n'
                'Current status: Department, degree, semester and regulation year illama exact credit verify panna mudiyadhu.\n'
                'Enga check pannanum: Unga regulation official curriculum/syllabus and department academic coordinator.\n'
                'Mukkiyam: Same subject name-ku regulation-wise credits maaralam.'
            ),
            'operational_general': (
                'Ketta detail: Campus operational information.\n'
                'Current status: Exact live detail verified indexed records-la illa.\n'
                'Next step: Department, academic year and date-oda relevant department office or campus helpdesk-la confirm pannunga.'
            ),
        }
        return replies.get(fact_id, answer)
    if language == 'ta':
        replies = {
            'operational_event': f'கேட்ட நிகழ்வு: {subject}.\nதற்போதைய நிலை: இந்தத் துறை மற்றும் தேதிக்கான சரிபார்க்கப்பட்ட நேரடி அறிவிப்பு பதிவுகளில் இல்லை.\nஎங்கே பார்க்க வேண்டும்: துறை அறிவிப்பு, தேர்வுகளுக்கு COE தளம், வேலைவாய்ப்பு நிகழ்வுகளுக்கு Placement Cell.\nஉறுதிப்படுத்த வேண்டியது: தேதி, நேரம், இடம், தகுதி மற்றும் அடையாள அட்டை அல்லது hall ticket.',
            'operational_facility': f'கேட்ட வசதி: {subject}.\nதற்போதைய நிலை: சரியான திறப்பு நேரம், மூடும் நேரம் அல்லது கட்டிட இடம் சரிபார்க்கப்பட்ட பதிவுகளில் இல்லை.\nஎங்கே உறுதிப்படுத்துவது: Campus directory அல்லது Security desk; நூலகத்திற்கு Library desk; விடுதிக்கு Hostel office; விளையாட்டிற்கு Physical Education department.',
            'operational_person': f'கேட்ட பணியாளர்: {subject}.\nகிடைக்கும் நேரம்: நேரடி duty schedule பதிவுகளில் வெளியிடப்படவில்லை.\nசரியான வழி: வருவதற்கு முன் தொடர்புடைய துறை அலுவலகத்தில் உறுதிப்படுத்துங்கள்; Principal-க்கு Administrative Office, hostel-க்கு Warden, placement-க்கு Placement Cell.',
            'operational_document': f'கேட்ட ஆவணம்: {subject}.\nதற்போதைய நிலை: சரியான வழங்கும் நேரம், கட்டணம் அல்லது அனுமதி விதி பதிவுகளில் இல்லை.\nஎங்கே தொடங்குவது: Department office அல்லது Class Advisor; தேர்வு ஆவணத்திற்கு COE; outpass-க்கு Warden; bus pass-க்கு Transport department.\nStudent ID மற்றும் தேவையான ஆதாரங்களை எடுத்துச் செல்லுங்கள்.',
            'operational_lab': f'கேட்ட கல்வி விவரம்: {subject}.\nதற்போதைய நிலை: சரியான manual, syllabus version அல்லது software list பதிவுகளில் இல்லை.\nஎங்கே பெறுவது: Department LMS அல்லது office; subject faculty அல்லது lab in-charge இடம் உறுதிப்படுத்துங்கள்.\nRegulation year, semester மற்றும் department-ஐ குறிப்பிடுங்கள்.',
            'operational_academic_rule': 'கேட்ட விவரம்: பாட credit தகவல்.\nதற்போதைய நிலை: Department, degree, semester மற்றும் regulation year இல்லாமல் சரியான credit-ஐ உறுதிப்படுத்த முடியாது.\nஉங்கள் regulation-க்கான official curriculum அல்லது syllabus-ஐ பார்த்து academic coordinator இடம் உறுதிப்படுத்துங்கள்.',
            'operational_general': 'கேட்ட விவரம்: Campus operational information.\nதற்போதைய நிலை: சரியான நேரடி விவரம் சரிபார்க்கப்பட்ட பதிவுகளில் இல்லை.\nDepartment, academic year மற்றும் தேதியுடன் தொடர்புடைய அலுவலகம் அல்லது campus helpdesk-ல் உறுதிப்படுத்துங்கள்.',
        }
        return replies.get(fact_id, answer)
    return answer


def operational_answer(question: str) -> dict | None:
    """Return structured guidance for a campus operational question."""
    if not question:
        return None

    if _DOCUMENT.search(question):
        item = _subject(_DOCUMENT, question, 'requested document')
        answer = (
            f'Request: {item}.\n'
            'Current status: The indexed official records do not publish a verified '
            'issue time, fee, or approval rule for this exact request.\n'
            'Where to start: Contact your department office or class advisor; exam '
            'documents should be confirmed with the Controller of Examinations, hostel '
            'outpass requests with the warden, and bus-pass requests with Transport.\n'
            'Take with you: Student ID and any supporting proof relevant to the request.\n'
            'Important: Do not rely on an unofficial deadline or fee without the current notice.'
        )
        return {'answer': _localized(answer, 'operational_document', question, item), 'fact_id': 'operational_document'}

    if _EVENT.search(question):
        event = _subject(_EVENT, question, 'event')
        answer = (
            f'Event requested: {event}.\n'
            'Current status: No verified notice matching the exact department and time '
            'in this question is available in the indexed records.\n'
            'Check first: Department notice or class group for department events; the '
            'Controller of Examinations portal for model or semester examinations; and '
            'the Placement Cell for placement drives.\n'
            'Confirm: Date, reporting time, venue, eligibility and required ID or hall ticket.\n'
            'Important: Words such as today, tomorrow and next week need a live dated notice.'
        )
        return {'answer': _localized(answer, 'operational_event', question, event), 'fact_id': 'operational_event'}

    if _PERSON.search(question):
        person = _subject(_PERSON, question, 'staff member')
        answer = (
            f'Person requested: {person}.\n'
            'Availability: A live duty schedule or room-presence status is not published '
            'in the indexed official records.\n'
            'Best route: Contact the relevant department office before visiting; for the '
            'Principal use the Administrative Office, for hostel matters use the warden, '
            'and for recruitment matters use the Placement Cell.\n'
            'Include: Your name, register number, department, purpose and preferred meeting time.'
        )
        return {'answer': _localized(answer, 'operational_person', question, person), 'fact_id': 'operational_person'}

    if _FACILITY.search(question):
        facility = _subject(_FACILITY, question, 'campus facility')
        answer = (
            f'Facility requested: {facility}.\n'
            'Current status: The exact live opening status, closing time or block-level '
            'location requested is not verified in the indexed records.\n'
            'How to confirm: Check the campus directory or security desk; use the Library '
            'desk for library hours, hostel office for hostel access, and Physical Education '
            'department for gym or sports-ground access.\n'
            'Important: Access can change on holidays, examination days and special-event days.'
        )
        return {'answer': _localized(answer, 'operational_facility', question, facility), 'fact_id': 'operational_facility'}

    if _LAB.search(question):
        lab = _subject(_LAB, question, 'lab material')
        answer = (
            f'Academic item requested: {lab}.\n'
            'Current status: The exact manual, syllabus version or installed-software list '
            'is not verified in the indexed records.\n'
            'Where to get it: Use the department LMS or department office and confirm with '
            'the subject faculty or lab in-charge.\n'
            'Confirm before use: Regulation year, semester, department and current academic year.'
        )
        return {'answer': _localized(answer, 'operational_lab', question, lab), 'fact_id': 'operational_lab'}

    if _ACADEMIC_RULE.search(question):
        answer = (
            'Request: Course credit information.\n'
            'Current status: A credit value cannot be verified without the applicable '
            'department, degree, semester and regulation year.\n'
            'Where to check: Use the official curriculum or syllabus for your regulation '
            'and confirm it with the department academic coordinator.\n'
            'Important: The same subject name can carry different credits across regulations.'
        )
        return {'answer': _localized(answer, 'operational_academic_rule', question), 'fact_id': 'operational_academic_rule'}

    return None
