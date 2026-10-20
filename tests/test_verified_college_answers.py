from src.core.verified_college_answers import lookup_verified_answer


def test_verified_answer_matches_punctuation_and_case():
    result = lookup_verified_answer('WHAT IS EGSPEC')
    assert result is not None
    assert result['answer'] == 'EGSPEC is E. G. S. Pillay Engineering College.'
    assert result['source_url'] == 'https://egspec.org/about/history'


def test_unverified_question_has_no_answer():
    assert lookup_verified_answer('What is the weather tomorrow?') is None


def test_tanglish_and_polite_paraphrases_match_verified_facts():
    name = lookup_verified_answer('College oda peru enna, please?')
    established = lookup_verified_answer('Could you tell me when the college was founded?')
    assert name is not None
    assert name['fact_id'] == 'college_name'
    assert name['answer'] == 'EGSPEC is E. G. S. Pillay Engineering College.'
    assert established is not None
    assert established['fact_id'] == 'established'


def test_engineering_overview_and_common_typo_are_verified():
    overview = lookup_verified_answer('Tell me about EGSPEC')
    typo = lookup_verified_answer('ok tell me about espec')
    assert overview is not None and overview['fact_id'] == 'engineering_overview'
    assert typo is not None and typo['fact_id'] == 'engineering_overview'
    assert '11 undergraduate' in overview['answer']
    assert 'NAAC A++' in typo['answer']


def test_student_feedback_does_not_invent_sentiment():
    result = lookup_verified_answer('anything negative feedback about this college')
    assert result is not None
    assert result['fact_id'] == 'student_feedback'
    assert 'do not publish an audited aggregate student rating' in result['answer']


def test_detailed_engineering_queries_use_structured_verified_facts():
    cases = {
        'Give EGSPEC placement details including package and recruiters': ('placements', '₹60 LPA'),
        'How can I join EGSPEC through TNEA and what cutoff is needed?': ('engineering_admission_tnea', '3806'),
        'scholarship eligibility': ('engineering_scholarships', 'Merit Scholarship'),
        'college bus route': ('engineering_transport', '25 bus routes'),
        'total students': ('engineering_student_count', '25,000+'),
    }
    for question, (fact_id, expected) in cases.items():
        result = lookup_verified_answer(question)
        assert result is not None and result['fact_id'] == fact_id
        assert expected in result['answer']


def test_transport_answer_has_all_routes_and_honest_schedule_limits():
    result = lookup_verified_answer('sirkali college bus route and timing')
    assert result and result['fact_id'] == 'engineering_transport'
    answer = result['answer']
    assert '1. Mannargudi' in answer
    assert '25. Mayiladuthurai' in answer
    assert '20. Sirkali — 7:10 AM' in answer
    assert '+91 75986 90315' in answer
    assert 'does not give stop-wise pickup times' in answer
    assert 'bus fees' in answer


def test_acknowledgements_do_not_trigger_document_retrieval():
    for message in ('ok nice', 'ok good', 'great'):
        result = lookup_verified_answer(message)
        assert result is not None
        assert result['fact_id'] == ''


def test_out_of_scope_follow_up_does_not_reuse_previous_fact():
    assert lookup_verified_answer(
        'What is the weather there?',
        context_fact_id='college_name',
    ) is None


def test_vague_follow_up_reuses_last_verified_institute_topic():
    result = lookup_verified_answer(
        'What about that?',
        context_fact_id='college_name',
    )
    assert result is not None
    assert result['fact_id'] == 'college_name'


def test_verified_answers_are_scoped_to_each_institution():
    pharmacy = lookup_verified_answer('Tell me about EGS Pillay College of Pharmacy')
    nursing = lookup_verified_answer('What courses are available in the Nursing college?')
    arts = lookup_verified_answer('What courses are available in EGS Pillay Arts and Science College?')
    polytechnic = lookup_verified_answer('Tell me about EGS Pillay Polytechnic College')

    assert pharmacy and 'B.Pharm' in pharmacy['answer'] and 'DGNM' not in pharmacy['answer']
    assert nursing and 'DGNM' in nursing['answer'] and 'B.Pharm' not in nursing['answer']
    assert arts and 'B.Sc Artificial Intelligence and Machine Learning' in arts['answer']
    assert polytechnic and 'DOTE' in polytechnic['answer']


def test_institution_introductions_explain_subject_college_and_scope():
    cases = {
        'Tell me about EGSPEC': ('What is Engineering?', '1995', 'Scope:'),
        'Tell me about EGS Pillay Arts and Science College': ('What is Arts & Science?', '1996', 'Scope by field:'),
        'Tell me about EGS Pillay College of Pharmacy': ('What is Pharmacy?', 'D.Pharm', 'Scope by course:'),
        'Tell me about EGS Pillay College of Nursing': ('What is Nursing?', 'DGNM', 'Scope:'),
        'Tell me about EGS Pillay Polytechnic College': ('What is a Polytechnic?', '2011', '2006'),
        'Tell me about EGS Pillay College of Education': ('What is Education/B.Ed?', '2014', 'Scope:'),
        'Tell me about EGS Pillay Naturopathy and Yoga Medical College': ('What is Naturopathy & Yoga?', 'BNYS', 'Scope:'),
        'Tell me about EGS Pillay International School': ('What is school education?', 'CBSE', 'Future scope:'),
    }
    for question, expected in cases.items():
        result = lookup_verified_answer(question)
        assert result is not None, question
        for phrase in expected:
            assert phrase in result['answer'], question
        if question == 'Tell me about EGSPEC':
            assert 'Sources:' not in result['answer']
            for department in (
                'Mechanical Engineering', 'Artificial Intelligence and Data Science',
                'Civil Engineering', 'Electrical and Electronics Engineering',
                'Electronics and Communication Engineering', 'Computer Science and Engineering',
                'Information Technology', 'Biomedical Engineering',
                'Computer Science and Business Systems', 'Cyber Security',
                'Artificial Intelligence and Machine Learning',
            ):
                assert department in result['answer']
        else:
            assert 'https://' in result['answer'], question


def test_subject_meaning_and_unrelated_weather_remain_distinct():
    assert 'What is Arts & Science?' in lookup_verified_answer('What is arts?')['answer']
    assert 'What is Arts & Science?' in lookup_verified_answer('Tell me about arts')['answer']
    assert 'What is Pharmacy?' in lookup_verified_answer('What is pahaemacy?')['answer']
    assert lookup_verified_answer('What is the weather tomorrow?') is None


def test_each_engineering_branch_includes_career_fields():
    for branch in ('AI & DS', 'CSE', 'IT', 'CSBS', 'BME', 'MECH', 'ECE', 'EEE', 'CIVIL', 'AIML'):
        answer = lookup_verified_answer(branch)
        assert answer is not None, branch
        assert 'Typical career fields:' in answer['answer'], branch
        assert 'not guaranteed placements' in answer['answer'], branch


def test_campus_detail_questions_have_specific_source_backed_answers():
    cases = {
        'college environment': ('engineering_environment', '1 Gbps'),
        'vision and mission': ('engineering_vision_mission', 'global centre'),
        'how do they teach': ('engineering_teaching', 'internship'),
        'pos and cos': ('engineering_po_co', 'Course Outcome'),
        'placement training': ('engineering_placement_training', 'aptitude'),
        'lab facilities': ('engineering_labs', '960 terminals'),
        'staffs epadi': ('engineering_staff', 'faculty'),
        'total blocks': ('engineering_blocks', 'GG Block'),
        'infrastructure site map': ('engineering_blocks', 'SJ Block'),
    }
    for question, (fact_id, phrase) in cases.items():
        result = lookup_verified_answer(question)
        assert result and result['fact_id'] == fact_id, question
        assert phrase.casefold() in result['answer'].casefold(), question
        assert result['source_url'].startswith('https://'), question


def test_reported_short_queries_use_verified_facts():
    from src.core.question_understanding import normalize_question
    cases = {
        'egspec': 'engineering_overview',
        'history': 'engineering_overview',
        'ok who is the cahir persaon': 'engineering_chairperson',
        'List all colleges under EGS Pillay Group': 'group_institutions',
        'Tell me about EGS Pillay Polytechnic diploma courses': 'polytechnic_overview',
        'List EGSPEC college bus routes and starting times': 'engineering_transport',
        'what are the courses': 'departments',
        'AI & DS': 'branch_aids',
        'CSE': 'branch_cse',
        'IT': 'branch_it',
        'CSBS': 'branch_csbs',
        'BME': 'branch_bme',
        'MECH': 'branch_mechanical',
        'ECE': 'branch_ece',
        'CiVIL': 'branch_civil',
        'AIML': 'branch_aiml',
        'EEE': 'branch_eee',
    }
    for question, fact_id in cases.items():
        result = lookup_verified_answer(normalize_question(question))
        assert result and result['fact_id'] == fact_id, question
