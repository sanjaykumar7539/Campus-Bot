import json
from pathlib import Path


def test_contact_facts_have_no_template_phone_numbers():
    root = Path(__file__).resolve().parents[1] / 'training'
    source = root / 'online-college-qa' / 'train.jsonl'
    facts = {row['fact_id']: row for row in map(json.loads, source.read_text(encoding='utf-8').splitlines())}
    expected = {
        'arts_science_admission_contact': ('egspasc.ac.in', '99768 88999'),
        'polytechnic_admission_contact': ('egsppc.ac.in', '252112'),
        'pharmacy_admission_contact': ('admissions.egspgroup.in', '99768 88999'),
    }
    for fact_id, (domain, phone) in expected.items():
        fact = facts[fact_id]
        assert domain in fact['source_url']
        assert phone in fact['answer']
        assert not any(bad in fact['answer'] for bad in ('98765 43210', '91234 56789', '99887 76655'))
    assert 'group contacts, not pharmacy-specific' in facts['pharmacy_admission_contact']['answer']
