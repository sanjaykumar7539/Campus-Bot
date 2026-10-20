"""Offline reviewed translations and consistent display for chat and voice.

Unknown translations are explicitly labelled English. A requested locale must
never be returned as metadata for an unchanged English answer.
"""
import re

from src.core.institution_guides import GUIDES
from src.core.verified_college_answers import verified_fact_record


LOCALIZED = {
    'engineering_admission_tnea': {
        'ta': '- TNEA code: 3806.\n- Counselling வழி: பதிவு, சான்றிதழ் சரிபார்ப்பு, rank, choice filling-ல் 3806 மற்றும் விரும்பும் பிரிவுகள், allotment கிடைத்தபின் reporting.\n- TNEA என்பது Tamil Nadu B.E./B.Tech single-window சேர்க்கை வழி.\n- நிலையான minimum/maximum cutoff இல்லை; ஆண்டு, பிரிவு, category, round மற்றும் காலியிடங்களைப் பொறுத்து மாறும்.\n- வாய்ப்பை மதிப்பிட cutoff, category, branch, year தேவை. தற்போதைய பதிவுகளில் உறுதிப்படுத்தப்பட்ட branch-wise closing-cutoff table இல்லை.\n- PG மற்றும் lateral-entryக்கு தனிச் சேர்க்கை நடைமுறைகள் உள்ளன.',
        'tanglish': '- TNEA code: 3806.\n- Counselling-la register panni certificate verification mudichu rank vaanganum; choice filling-la 3806 and preferred branches select panni allotment-ku apram report pannanum.\n- TNEA Tamil Nadu B.E./B.Tech single-window admission route.\n- Fixed minimum/maximum cutoff illa; year, branch, category, round, seat availability poruthu maarum.\n- Chance estimate-ku cutoff, category, branch, year thevai. Verified branch-wise closing-cutoff table current records-la illa.\n- PG/lateral-entry-ku separate admission procedure irukku.',
    },
    'engineering_scholarships': {
        'ta': '- Merit Scholarship பக்கமும் 2026–27 விளம்பரமும் cutoff அடிப்படையிலான உதவித்தொகையை விவரிக்கின்றன; Sigaram Scholarship 2026 குறிப்பிடப்பட்டுள்ளது.\n- SC/ST Cell, தகுதியுள்ள அரசு/அரசு சாரா திட்டங்கள் பற்றிய விழிப்புணர்வு அளிப்பதாகக் கூறுகிறது.\n- எல்லாத் திட்டங்களுக்கும் முழுமையான cutoff slab, income limit, category rule, தொகை வெளியிடப்படவில்லை. நடப்பு notice மற்றும் உங்கள் தகுதி விவரங்களுடன் சரிபார்க்க வேண்டும்.\n- பொதுவான சரிபார்ப்புக்கான ஆவணங்கள்: mark sheets, community/income certificates, bank details மற்றும் பொருந்தும் eligibility certificate; திட்டத்தைப் பொறுத்து பட்டியல் மாறும்.',
        'tanglish': '- Merit Scholarship page and 2026–27 advertisement-la cutoff-based scholarship mention pannirukku; Sigaram Scholarship 2026-um promote pannirukku.\n- SC/ST Cell eligible government/non-government schemes pathi awareness kudukkudhu-nu site solludhu.\n- Ella scheme-kum complete cutoff slab, income limit, category rule, amount publish pannala. Current notice-oda unga eligibility compare pannanum.\n- Common verification documents: mark sheets, community/income certificates, bank details, relevant eligibility certificate; exact list scheme-a poruthadhu.',
    },
    'engineering_event_timing': {
        'ta': '- நிலையான ஆண்டு sports/cultural season அதிகாரப்பூர்வ பதிவுகளில் உறுதியாகவில்லை; ஆண்டு மற்றும் ஏற்பாட்டாளரைப் பொறுத்துத் தேதிகள் மாறும்.\n- பழைய உதாரணங்கள்: Aksharam 27 March 2025; 2026 reports-ல் April, May, June, September நிகழ்வுகள்; student symposium 10 October 2026. இவை எதிர்காலத் தேதி உறுதிகள் அல்ல.\n- Sports சாதனைகள் 2024–25, 2025–26 அடிப்படையில் உள்ளன; Energy 2025 பக்கம் அடுத்த போட்டித் தேதியை உறுதி செய்யவில்லை.\n- நடப்பு calendar, sports department, club notices-ல் registration deadline மற்றும் venue சரிபார்க்கவும்.',
        'tanglish': '- Fixed yearly sports/cultural season official records-la establish aagala; academic year/organizer poruthu dates maarum.\n- Past examples: Aksharam 27 March 2025; 2026 reports-la April, May, June, September events; student symposium 10 October 2026. Idhu future date promise illa.\n- Sports achievements 2024–25, 2025–26 year-wise irukku; Energy 2025 page-la next edition date confirm pannala.\n- Current calendar, sports department, club notices-la registration deadline and venue check pannunga.',
    },
    'engineering_overview': {
        'ta': '- பொறியியல் என்பது கணிதம் மற்றும் அறிவியலைப் பயன்படுத்தித் தொழில்நுட்பம், அமைப்புகள் மற்றும் கட்டமைப்புகளை வடிவமைத்து மேம்படுத்தும் படிப்பு.\n'
              '- E.G.S. Pillay Engineering College, Nagapattinam, 1995ல் தொடங்கப்பட்டது. நிறுவனர் Dr. Chev. G.S. Pillay; G.S. Pillay & Sons Charitable and Educational Trust நிர்வகிக்கிறது. 2002ல் Anna University இணைப்பு, 2017ல் தன்னாட்சி பெற்றது. அதிகாரப்பூர்வ தளம் தலைவர் Smt. S. Jothimani G.S. Pillay என்று குறிப்பிடுகிறது.\n'
              '- 11 இளநிலைப் படிப்புகள்:\n{branches}\n'
              '- முதுநிலை மற்றும் ஆராய்ச்சி வாய்ப்புகளும் உள்ளன; கல்லூரி NAAC A++ அங்கீகாரத்தைத் தெரிவிக்கிறது.\n'
              '- வேலைத் துறைகள்: CSE/IT — மென்பொருள், cloud; AI/DS — தரவு, AI; CSBS — வணிகத் தொழில்நுட்பம்; Cyber Security — தகவல் பாதுகாப்பு; ECE — மின்னணு, தொடர்பியல்; EEE — மின்சாரம், automation; Mechanical — உற்பத்தி; Civil — கட்டுமானம்; Biomedical — மருத்துவக் கருவிகள். வேலை கிடைப்பது உறுதி அல்ல.',
        'tanglish': '- Engineering-na maths/science use panni technology, systems and infrastructure design/improve panra padippu.\n'
                    '- E.G.S. Pillay Engineering College, Nagapattinam, 1995-la start aachu. Dr. Chev. G.S. Pillay founder; G.S. Pillay & Sons Charitable and Educational Trust manage pannudhu. Anna University affiliation 2002; autonomous status 2017. Official site-la Smt. S. Jothimani G.S. Pillay Chairman-nu irukku.\n'
                    '- 11 UG programmes irukku:\n{branches}\n'
                    '- PG/research opportunities-um irukku; college NAAC A++ accreditation report pannudhu.\n'
                    '- Scope: CSE/IT software/cloud; AI/DS data/AI; CSBS business technology; Cyber Security information security; ECE electronics/communication; EEE power/automation; Mechanical manufacturing; Civil construction; Biomedical medical devices. Idhu possible career fields; job guarantee illa.',
    },
    'arts_science_overview': {
        'ta': '- Arts & Science என்பது மொழிகள், வணிகம், மேலாண்மை, கணினி மற்றும் அறிவியல் சார்ந்த படிப்புகள்.\n- Edayathangudy G.S. Pillay Arts & Science College, Thethi, Nagapattinam, 1996ல் தொடங்கியது. Bharathidasan University இணைப்பு; அதிகாரப்பூர்வ வரலாறு தன்னாட்சி மற்றும் NAAC A நிலையை விவரிக்கிறது.\n- BA Tamil/English/Defence Studies, BCom, BBA, BSc பிரிவுகள், BCA மற்றும் முதுநிலை/ஆராய்ச்சிப் படிப்புகள் குறிப்பிடப்பட்டுள்ளன. தேர்ந்தெடுத்த படிப்பின் தற்போதைய இடங்களை உறுதிப்படுத்துங்கள்.\n- மொழிகள்: கற்பித்தல்/மொழிபெயர்ப்பு; வணிகம்: கணக்கியல்/வங்கி; கணினி: மென்பொருள்/தரவு; அறிவியல்: ஆய்வகம்/ஆராய்ச்சி; visual communication/fashion: ஊடகம்/வடிவமைப்பு. சில பணிகளுக்கு கூடுதல் தகுதி தேவை.',
        'tanglish': '- Arts & Science-na languages, commerce, management, computing and science padippugal.\n- Edayathangudy G.S. Pillay Arts & Science College, Thethi, Nagapattinam, 1996-la start aachu; Bharathidasan University affiliation irukku. Official history-la autonomous status and NAAC A mention pannirukku.\n- BA Tamil/English/Defence Studies, BCom, BBA, BSc branches, BCA, PG/research options irukku. Current course intake confirm pannunga.\n- Scope: languages teaching/translation; commerce accounting/banking; computing software/data; science labs/research; visual communication/fashion media/design. Sila roles-ku extra qualification thevai.',
    },
    'pharmacy_overview': {
        'ta': '- Pharmacy என்பது மருந்துகளின் தயாரிப்பு, பாதுகாப்பான பயன்பாடு, தரம் மற்றும் விநியோகம் பற்றிய படிப்பு.\n- EGS Pillay College of Pharmacy: D.Pharm — 2 ஆண்டுகள், வெளியிடப்பட்ட intake 60; B.Pharm — 4 ஆண்டுகள், intake 100, lateral-entry வாய்ப்பு; Pharm.D — 6 ஆண்டுகள், intake 30; M.Pharm — 2 ஆண்டுகள்.\n- M.Pharm பிரிவுகள்: Pharmaceutics, Pharmaceutical Analysis, Pharmacology.\n- வாய்ப்புகள்: community/hospital pharmacy, உற்பத்தி, quality control, regulatory affairs, ஆராய்ச்சி, clinical pharmacy. பதிவு மற்றும் பணித் தகுதிகளைச் சரிபார்க்க வேண்டும். தொடங்கிய ஆண்டு/தற்போதைய தலைவர் மேற்கோள் course page மூலம் உறுதியாகவில்லை.',
        'tanglish': '- Pharmacy-na medicines preparation, safe use, quality and distribution pathi padikkaradhu.\n- EGS Pillay College of Pharmacy-la D.Pharm 2 years/intake 60; B.Pharm 4 years/intake 100, lateral-entry option; Pharm.D 6 years/intake 30; M.Pharm 2 years-nu published details irukku.\n- M.Pharm branches: Pharmaceutics, Pharmaceutical Analysis, Pharmacology.\n- Scope: community/hospital pharmacy, manufacturing, quality control, regulatory affairs, research, clinical pharmacy. Registration/job eligibility check pannunga. Founder year/current chairman indha course page-la verify aagala.',
    },
    'nursing_overview': {
        'ta': '- Nursing என்பது நோயாளிப் பராமரிப்பு, உடல்நிலை மதிப்பீடு, சிகிச்சை உதவி மற்றும் சுகாதாரக் கல்வி சார்ந்த படிப்பு.\n- EGS Pillay nursing சேர்க்கைப் பக்கம் B.Sc Nursing, DGNM, clinical training, labs மற்றும் simulation kits-ஐக் குறிப்பிடுகிறது.\n- அதே பக்கம் INC recognition மற்றும் placement assistance என்று தெரிவிக்கிறது; உதவி என்பது வேலை உறுதி அல்ல.\n- வாய்ப்புகள்: மருத்துவமனை, சமூக/பொதுச் சுகாதாரம், பின்னர் சிறப்புப் பயிற்சி அல்லது nursing education; பதிவு/கூடுதல் தகுதிகள் தேவைப்படலாம். தொடங்கிய ஆண்டு/தற்போதைய தலைவர் இப்பக்கத்தில் உறுதிப்படுத்தப்படவில்லை.',
        'tanglish': '- Nursing-na patient care, health assessment, treatment support and health education padippu.\n- EGS Pillay nursing admission page-la B.Sc Nursing, DGNM, clinical training, labs and simulation kits irukku-nu sollirukku.\n- INC recognition and placement assistance-nu page state pannudhu; assistance job guarantee illa.\n- Scope: hospital nursing, community/public health, later specialization/nursing education. Registration and extra qualifications thevai padalam. Founding year/current chairman indha page-la verify aagala.',
    },
    'polytechnic_overview': {
        'ta': '- Polytechnic என்பது செய்முறைத் திறன், workshop மற்றும் technician பணிகளுக்கான diploma வழி; விதிகளுக்குட்பட்டு degree lateral entry வாய்ப்பு இருக்கலாம்.\n- E.G.S. Pillay Polytechnic College, G.S. Pillay & Sons Charitable and Educational Trust கீழ் இயங்குகிறது; DOTE Tamil Nadu இணைப்பு குறிப்பிடப்பட்டுள்ளது.\n- 3 ஆண்டு diplomas: Computer, ECE, Instrumentation & Control, EEE, Mechanical Engineering.\n- நிறுவனர் Dr. Chev. G.S. Pillay; principal பக்கம் Thiru A. Dhanasekar-ஐக் குறிப்பிடுகிறது. தொடங்கிய ஆண்டு குறித்து footer 2006 என்றும் principal message 2011 என்றும் முரண்படுகின்றன.\n- வாய்ப்புகள்: IT support, electronics, industrial controls, electrical maintenance, manufacturing; பொருந்தும் விதிகளின்படி மேல்படிப்பு.',
        'tanglish': '- Polytechnic-na practical skills/workshop based diploma route; rules-ku etha maari degree lateral entry option irukkalam.\n- E.G.S. Pillay Polytechnic College trust management-la DOTE Tamil Nadu affiliation-oda irukku-nu site solludhu.\n- 3-year diplomas: Computer, ECE, Instrumentation & Control, EEE, Mechanical Engineering.\n- Founder Dr. Chev. G.S. Pillay; principal page-la Thiru A. Dhanasekar name irukku. Founding year footer-la 2006, principal message-la 2011; college-kitta confirm pannunga.\n- Scope: IT support, electronics, industrial controls, electrical maintenance, manufacturing and eligible higher studies.',
    },
    'education_overview': {
        'ta': '- B.Ed என்பது கற்பித்தல், பாடத் திட்டமிடல், வகுப்பறைப் பயிற்சி மற்றும் மாணவர் மதிப்பீட்டிற்கான படிப்பு.\n- EGS Pillay College of Education தளம் 2014 முதல் இயங்குவதாகவும் B.Ed annual intake 100 என்றும் தெரிவிக்கிறது.\n- Tamil Nadu Government/NCTE அனுமதி, Tamil Nadu Teachers Education University இணைப்பு, code 11316 என்று தளம் குறிப்பிடுகிறது.\n- ஆசிரியர் பணிக்கு பொருந்தும் தகுதி/நியமன விதிகளைப் பூர்த்தி செய்ய வேண்டும்; B.Ed மட்டும் வேலை உறுதி அல்ல. தனித்த நிறுவனர்/தற்போதைய தலைவர் தகவல் இப்பக்கத்தில் உறுதியாகவில்லை.',
        'tanglish': '- B.Ed-na teaching, lesson planning, classroom practice and student assessment padippu.\n- EGS Pillay College of Education site-la 2014-lendhu operate pannudhu, B.Ed annual intake 100-nu irukku.\n- Tamil Nadu Government/NCTE permission, Tamil Nadu Teachers Education University affiliation, code 11316-nu site solludhu.\n- Teacher job-ku applicable eligibility/recruitment rules meet pannanum; B.Ed mattum job guarantee illa. Founder/current chairman details cited page-la verify aagala.',
    },
    'naturopathy_overview': {
        'ta': '- Naturopathy & Yoga என்பது வாழ்க்கைமுறை, yoga மற்றும் மருந்தில்லா wellness அணுகுமுறைகள் சார்ந்த படிப்பு; clinical practice அங்கீகரிக்கப்பட்ட தகுதி மற்றும் பொருந்தும் விதிகளைப் பொறுத்தது.\n- EGS Pillay Group directory, EGS Pillay Naturopathy and Yoga Medical College மற்றும் BNYS-ஐப் பட்டியலிடுகிறது.\n- தனிக் கல்லூரி தளம் கடைசி சரிபார்ப்பில் கிடைக்கவில்லை; தொடங்கிய ஆண்டு, தற்போதைய தலைவர், intake, fees, approvals உறுதிப்படுத்தப்படவில்லை.\n- வாய்ப்புகள் தகுதி/பதிவைப் பொறுத்து wellness, yoga, health education மற்றும் மேல்படிப்பு; பட்டப்பெயரை வைத்து licence அல்லது வேலை உறுதி எனக் கருதக்கூடாது.',
        'tanglish': '- Naturopathy & Yoga-na lifestyle, yoga and non-drug wellness approaches padikkaradhu; clinical practice recognized qualification/rules-a poruthadhu.\n- EGS Pillay Group directory-la Naturopathy and Yoga Medical College, BNYS list pannirukku.\n- Separate site last check-la available illa; founding year, leadership, intake, fees, approvals verify aagala.\n- Qualification/registration-ku etha maari wellness, yoga, health education, higher studies explore pannalam; degree name mattum licence/job guarantee illa.',
    },
    'school_overview': {
        'ta': '- பள்ளிக் கல்வி மொழி, கணிதம், அறிவியல், சமூகப் பாடங்கள் மற்றும் அடிப்படைத் திறன்களை வளர்க்கிறது.\n- EGS Pillay Group directory, International School-ஐ CBSE curriculum பள்ளியாகக் குறிப்பிடுகிறது.\n- தொடங்கிய ஆண்டு, தற்போதைய தலைவர், சரியான class range மற்றும் fees மேற்கோள் பக்கத்தில் உறுதிப்படுத்தப்படவில்லை.\n- அடுத்த கல்விப் பாதை பள்ளியில் உண்மையில் வழங்கப்படும் வகுப்புகள்/பாடத்திட்டத்தைப் பொறுத்தது; தொழில்முறைப் பணிகளுக்கு மேல்படிப்பு தேவை.',
        'tanglish': '- School education-na languages, maths, science, social subjects and basic skills build panradhu.\n- EGS Pillay Group directory-la International School CBSE curriculum school-nu irukku.\n- Founding year, current chairman, exact class range and fees cited page-la verify aagala.\n- Adutha study options school actually offer panra classes/curriculum-a poruthadhu; professional careers-ku further education thevai.',
    },
    'engineering_sports': {
        'ta': '- அதிகாரப்பூர்வ Physical Education பக்கம் cricket, basketball, badminton, hockey, tennis, volleyball-ஐக் குறிப்பிடுகிறது; சாதனைப் பதிவுகளில் chess, kabaddi, table tennis, handball, athletics உள்ளன.\n- 2024–25, 2025–26 சாதனைப் பதிவுகளும் inter-college முடிவுகளும் வெளியிடப்பட்டுள்ளன. Energy 2025 குழு போட்டியில் football உள்ளிட்ட விளையாட்டுகள் குறிப்பிடப்பட்டுள்ளன.\n- விளையாட்டுத் துறையில் ஆர்வமுள்ள மாணவர்களுக்கு சிறப்புப் பயிற்சி அளிப்பதாகத் தளம் கூறுகிறது; selection அல்லது scholarship உறுதி அல்ல.\n- Physical Education Director: Mr. D. Velavan, +91 99429 97667. தற்போதைய trials, practice time, facilities, sports-quota விதிகளைத் துறையிடம் உறுதிப்படுத்துங்கள்.\n- நிலையான ஆண்டு sports season அல்லது அடுத்த போட்டித் தேதி இப்பதிவுகளில் உறுதியாகவில்லை; நடப்பு notice தேவை.',
        'tanglish': '- Official sports page-la cricket, basketball, badminton, hockey, tennis, volleyball irukku; achievements-la chess, kabaddi, table tennis, handball, athletics-um irukku.\n- 2024–25, 2025–26 achievements/inter-college results publish pannirukku. Group Energy 2025 tournament-la football-um mention pannirukku.\n- Sports career interest irukkura students-ku special training-nu college solludhu; selection/scholarship guarantee illa.\n- Physical Education Director Mr. D. Velavan: +91 99429 97667. Current trials, practice time, facilities, sports quota rules confirm pannunga.\n- Fixed yearly season illa next tournament date indha records-la establish aagala; current notice check pannunga.',
    },
}


def display_answer(result, language):
    """Return rendered text and its actual language; keep source metadata intact."""
    original = result['answer']
    answer = '\n'.join(line for line in original.splitlines()
                       if not re.match(r'^\s*[-*]?\s*Sources?:', line, re.I)).strip()
    if language == 'en':
        return answer, 'en'
    direct = result.get('localized_answers', {}).get(language)
    if direct:
        return direct, language
    fact_id = result.get('fact_id')
    translations = LOCALIZED.get(fact_id, {})
    fact = verified_fact_record(fact_id) if fact_id else None
    # A fee or focused follow-up can retain its institution's overview ID.
    # Translate only the original full fact/guide, never overwrite the answer.
    if language in translations and original in {GUIDES.get(fact_id, ''), fact['answer'] if fact else ''}:
        branches = '\n'.join(line for line in GUIDES.get('engineering_overview', '').splitlines()
                             if re.match(r'^\s+\d+\.', line))
        return translations[language].replace('{branches}', branches), language
    if language == 'ta' and re.search(r'[\u0b80-\u0bff]', answer):
        return answer, language
    if language == 'tanglish' and re.search(r'\b(?:pannunga|irukku|thevai|sollunga)\b', answer, re.I):
        return answer, language
    notice = {
        'ta': 'இந்தப் பதிலின் சரிபார்க்கப்பட்ட தமிழ் மொழிபெயர்ப்பு இன்னும் இல்லை; கிடைக்கும் ஆங்கில விவரம் கீழே.',
        'tanglish': 'Indha answer-ku reviewed Tanglish translation innum illa; available English details keezha irukku.',
    }.get(language, 'A reviewed translation is unavailable for this answer; the English details follow.')
    return notice + '\n\n' + answer, 'en'
