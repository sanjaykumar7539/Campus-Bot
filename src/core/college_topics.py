"""Local topic expansion for English, Tamil and common Tanglish questions."""
import re
TOPICS = {'Hostel': ('hostel accommodation mess rooms', ('hostel', 'accommodation', 'mess', 'விடுதி', 'தங்கும்')), 'Placements': ('placement recruiters companies jobs salary', ('placement', 'placements', 'recruit', 'salary', 'வேலைவாய்ப்பு', 'வேலை வாய்ப்பு')), 'Transport': ('transport college bus routes timings', ('transport', 'bus', 'பேருந்து', 'போக்குவரத்து')), 'Facilities': ('library laboratory labs facilities campus', ('library', 'laboratory', 'labs', 'facilities', 'நூலகம்', 'ஆய்வகம்', 'வசதி')), 'Faculty': ('faculty professors teachers staff head department', ('faculty', 'professor', 'teacher', 'hod', 'staff', 'ஆசிரியர்', 'பேராசிரியர்')), 'Scholarships': ('scholarship financial aid eligibility', ('scholarship', 'financial aid', 'உதவித்தொகை')), 'Examinations': ('examination exam results timetable schedule', ('exam', 'result', 'timetable', 'தேர்வு', 'முடிவு')), 'Updates': ('news events notices announcements updates', ('latest', 'update', 'news', 'event', 'notice', 'செய்தி', 'நிகழ்ச்சி', 'அறிவிப்பு')), 'Admissions': ('admission application eligibility intake', ('admission', 'apply', 'eligibility', 'சேர்க்கை')), 'Fees': ('fees tuition cost payment', ('fee', 'tuition', 'cost', 'fees evlo', 'கட்டணம்')), 'Courses': ('courses departments programs degrees', ('course', 'department', 'program', 'படிப்பு', 'பாடப்பிரிவு', 'துறை'))}
def topics_for(query):
    lowered = query.casefold()
    return {name for name, (_, aliases) in TOPICS.items()
            if any((re.search(r'(?<![a-z])' + re.escape(alias) + r'(?![a-z])', lowered)
                    if alias.isascii() else alias in lowered) for alias in aliases)}
def expand_question(query):
    topics = topics_for(query)
    if not topics:
        return query
    return query + ' ' + ' '.join(TOPICS[name][0] for name in TOPICS if name in topics)
