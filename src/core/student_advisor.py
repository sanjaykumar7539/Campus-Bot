"""Bounded counselling intents composed from existing verified records."""
import re

from .college_scope import mentioned_colleges, requested_colleges
from .verified_college_answers import verified_fact_college, verified_fact_record


def _result(answer, fact_id=None, records=(), localized=None):
    sources = [{'document': record['source_url'], 'page': 'verified college Q&A',
                'relevance_score': 1.0} for record in records if record]
    return dict(answer=answer, sources=sources, confidence=1.0 if sources else 0.0,
                is_grounded=True, reason='Student guidance with explicit evidence limits',
                fact_id=fact_id, localized_answers=localized or {})


def student_advice(question, context_fact_id=None):
    lower = question.casefold()
    explicit = mentioned_colleges(question)
    previous = verified_fact_college(context_fact_id)
    colleges = explicit or ({previous} if previous else requested_colleges(question))
    college = next(iter(colleges)) if len(colleges) == 1 else None
    if re.search(r'\b(?:guarantee\w*|definitely|sure|assured|100\s*%)\b', lower) and re.search(r'\b(?:job|placement|employment|salary)\b', lower):
        return _result(
            '- A course or degree does not guarantee a job or a particular salary.\n'
            '- Compare your interests, curriculum, practical projects, internships and placement training.\n'
            '- Placement highlights describe past outcomes; individual results depend on skills, eligibility, interviews and available roles.\n'
            '- Tell me the institution and course you are considering so I can explain its verified options.',
            context_fact_id, localized={
                'ta': '- எந்தப் படிப்பும் வேலையையோ குறிப்பிட்ட சம்பளத்தையோ உறுதி செய்யாது.\n- உங்கள் ஆர்வம், பாடத்திட்டம், செய்முறைப் பயிற்சி, திட்டப்பணி மற்றும் வேலைவாய்ப்புப் பயிற்சியை ஒப்பிடுங்கள்.\n- வேலை கிடைப்பது திறன், தகுதி, நேர்முகத் தேர்வு மற்றும் காலிப் பணியிடங்களைப் பொறுத்தது.\n- எந்த நிறுவனம், எந்தப் படிப்பு என்பதைச் சொல்லுங்கள்.',
                'tanglish': '- Endha course-um job illa specific salary guarantee panna mudiyadhu.\n- Unga interest, syllabus, practical projects, internships, placement training compare pannunga.\n- Job kidaikkaradhu skills, eligibility, interview and available roles-a poruthadhu.\n- Endha institute/course consider panreenga-nu sollunga.',
            })
    if re.search(r'\b(?:new student|(?:choose|choosing|select|shortlist).*(?:course|career|degree|college|institution)|suitable course|which course.*(?:me|best)|help.*join|join.*help)\b', lower):
        return _result(
            '- I can help you shortlist a suitable institution and course.\n'
            '- Qualification: Have you completed 10th, 12th, a diploma or a degree? What subjects and marks/cutoff do you have?\n'
            '- Interests: Which subjects or career fields do you enjoy? If unsure, tell me what you like studying.\n'
            '- Budget and travel: What is your yearly budget, and do you need a hostel or daily bus?\n'
            '- Next: Share those details and your preferred institution. We can compare course scope, verified eligibility, admission steps and available scholarships.',
            context_fact_id, localized={
                'ta': '- உங்களுக்கேற்ற நிறுவனம் மற்றும் படிப்பைத் தேர்ந்தெடுக்க உதவுகிறேன்.\n- 10ஆம் வகுப்பு, 12ஆம் வகுப்பு, டிப்ளமா அல்லது பட்டப்படிப்பு முடித்துள்ளீர்களா? பாடங்கள், மதிப்பெண்கள் மற்றும் cutoff என்ன?\n- எந்தப் பாடங்கள் அல்லது வேலைத் துறைகளில் ஆர்வம் உள்ளது?\n- ஆண்டு செலவுத்திட்டம் என்ன? விடுதி அல்லது தினசரி பேருந்து தேவையா?\n- இவற்றையும் விரும்பும் நிறுவனத்தையும் சொன்னால் படிப்பு வாய்ப்புகள், தகுதி, சேர்க்கை மற்றும் உதவித்தொகைகளை ஒப்பிடலாம்.',
                'tanglish': '- Unga needs-ku suitable institute/course shortlist panna help panren.\n- Neenga 10th, 12th, diploma illa degree mudichirukeengala? Subjects, marks/cutoff enna?\n- Endha subjects/career fields-la interest irukku?\n- Yearly budget evlo? Hostel illa daily bus venuma?\n- Indha details-um preferred institute-um sollunga; course scope, eligibility, admission steps, scholarships compare pannalam.',
            })
    if college == 'engineering' and re.search(r'\b(?:cutoff|cut off|tnea)\b', lower) and (
        re.search(r'\d', lower) or re.search(r'\b(?:chance|definitely|guarantee|sure)\b', lower)
    ):
        fact = verified_fact_record('engineering_admission_tnea')
        from src.utils.answer_presentation import LOCALIZED
        localized = {
            'ta': '- Cutoff மதிப்பெண்ணை மட்டும் வைத்து குறிப்பிட்ட பிரிவில் சேர்க்கையை உறுதி செய்ய முடியாது.\n- உங்கள் cutoff, category/quota, விரும்பும் பிரிவு, சேர்க்கை ஆண்டு தேவை; நீங்கள் சொன்ன மதிப்பெண் அதிகாரப்பூர்வ closing cutoff அல்ல.\n',
            'tanglish': '- Cutoff mark mattum vechu branch admission guarantee panna mudiyadhu.\n- Unga cutoff, category/quota, branch and admission year thevai; neenga sonna mark official closing cutoff illa.\n',
        }
        localized = {language: text + LOCALIZED[fact['fact_id']][language]
                     for language, text in localized.items()}
        return _result(
            '- I cannot guarantee admission to a branch from a cutoff mark alone.\n'
            '- Closing cutoffs depend on admission year, community/category, quota, counselling round and seat availability.\n'
            '- Tell me your cutoff, category/quota, preferred branch and admission year. Your supplied mark is not an official closing cutoff.\n'
            '- The indexed records do not contain a verified year-specific branch closing-cutoff table; an exact chance cannot be confirmed.\n'
            + fact['answer'], fact['fact_id'], [fact], localized=localized)
    admissions = bool(re.search(r'\b(?:admission|admissions|join|apply)\b', lower))
    documents = bool(re.search(r'\b(?:documents?|certificates?)\b', lower))
    scholarships = bool(re.search(r'\b(?:scholarships?|financial aid)\b', lower))
    if sum((admissions, documents, scholarships)) >= 2:
        records, parts = [], []
        if admissions:
            key = {'engineering': 'engineering_admission_tnea',
                   'polytechnic': 'polytechnic_admission'}.get(college)
            fact = verified_fact_record(key)
            parts.append('Admissions\n' + (fact['answer'] if fact else
                         '- Tell me the institution, course and entry qualification so I can identify the relevant admission route.'))
            if fact:
                records.append(fact)
        if documents:
            parts.append('Documents\n- Preparation checklist: mark sheets, identity proof, transfer certificate, and category/income certificates where applicable.\n'
                         '- This is general preparation guidance; the exact required documents must be checked against the course and admission-year notice.')
        if scholarships:
            fact = verified_fact_record('engineering_scholarships') if college == 'engineering' else None
            parts.append('Scholarships\n' + (fact['answer'] if fact else
                         '- Scheme eligibility and amounts need a current institution-specific notice. Share your course, marks and relevant eligibility category; do not assume an award is guaranteed.'))
            if fact:
                records.append(fact)
        localized = {}
        if college == 'engineering':
            from src.utils.answer_presentation import LOCALIZED
            documents_local = {
                'ta': '- ஆவணத் தயாரிப்பு: mark sheets, identity proof, transfer certificate மற்றும் பொருந்தினால் community/income certificates.\n- இது பொதுவான தயாரிப்பு வழிகாட்டல்; சரியான required list படிப்பு/ஆண்டு notice-ல் உறுதிப்படுத்த வேண்டும்.',
                'tanglish': '- Documents preparation: mark sheets, identity proof, transfer certificate, applicable community/income certificates.\n- Idhu general preparation guidance; exact required list course/year notice-la confirm pannanum.',
            }
            for language in ('ta', 'tanglish'):
                sections = []
                if admissions:
                    sections.append(LOCALIZED['engineering_admission_tnea'][language])
                if documents:
                    sections.append(documents_local[language])
                if scholarships:
                    sections.append(LOCALIZED['engineering_scholarships'][language])
                localized[language] = '\n\n'.join(sections)
        return _result('\n\n'.join(parts), records[0]['fact_id'] if records else context_fact_id, records, localized)
    if college and college != 'engineering':
        if re.search(r'\b(?:fees?|tuition|cost)\b', lower) and not re.search(r'\b(?:courses?|program(?:me)?s?|branches|duration|intake)\b', lower):
            from .conversation_context import _LABELS
            label = _LABELS[college]
            return _result(f'- I could not verify a current fee amount for {label} from the available records.\n'
                           '- Which course, admission year and quota do you mean?\n'
                           '- Compare tuition, exam fees, hostel/transport and other charges in the current official fee notice.',
                           context_fact_id, localized={
                               'ta': f'- {label}: தற்போதைய கட்டணத் தொகை கிடைக்கும் பதிவுகளில் உறுதிப்படுத்தப்படவில்லை.\n- எந்தப் படிப்பு, சேர்க்கை ஆண்டு மற்றும் quota என்பதைச் சொல்லுங்கள்.\n- நடப்பு கட்டண அறிவிப்பில் tuition, exam, hostel/transport மற்றும் பிற கட்டணங்களைத் தனித்தனியாகச் சரிபார்க்கவும்.',
                               'tanglish': f'- {label}: current fee amount available records-la verify aagala.\n- Endha course, admission year, quota-nu sollunga.\n- Current official notice-la tuition, exam, hostel/transport and other charges separate-a check pannunga.',
                           })
        if re.search(r'\bnba\b', lower):
            result = _result(f'- I cannot verify NBA accreditation for the requested {college} program from the available institution-specific records.\n'
                           '- Engineering-college accreditation cannot be transferred to a different institution or program.\n'
                           '- Check the exact program and validity period in its official accreditation record.', context_fact_id)
            result.update(is_grounded=False, reason='Specific detail not verified')
            return result
    if re.fullmatch(r'(?:what about (?:its |the )?)?fees?\??', lower) and not explicit and not previous:
        return _result('- Which institution, course and admission year do you mean?\n'
                       '- Include whether you need hostel or transport fees so I can identify the relevant charges.')
    return None
