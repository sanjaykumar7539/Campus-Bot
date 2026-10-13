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
