"""Build grounded multi-institution SFT data with explicit negative scope examples."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'training' / 'online-college-qa' / 'train.jsonl'
OUTPUT = ROOT / 'training' / 'all-institutions-grounded-qa-v2'
FALLBACK = 'Verified information for the requested college is unavailable.'

ANGLE_QUESTIONS = {
    'departments': ['Engineering departments'],
    'nba_programs_scope': ['Which courses are NBA accredited and what is their scope?'],
    'nirf_2025': ['What is the NIRF 2025 rank band?'],
    'research_centers': ['Which departments have recognized research centers?'],
    'examinations': ['Examinations'],
    'arts_science_overview': [
        'Arts science departments', 'Arts Science UG PG programs',
        'Arts Science research programs', 'EGS Pillay Arts Science courses',
    ],
    'pharmacy_overview': [
        'Pharmacy courses enna?', 'Pharmacy duration and intake',
        'Pharmacy eligibility details', 'M Pharm branches',
        'parmachy college details sollu',
    ],
    'nursing_overview': [
        'B sc nursing DGNM details', 'Nursing facilities and clinical training',
        'Is Nursing INC recognized?', 'Nursing placement assistance',
        'nurshibg courses enna',
    ],
    'polytechnic_overview': [
        'Polytechnic branches', 'Polytechnic aided and self financing branches',
        'Polytechnic DOTE approval', 'Diploma duration in Polytechnic',
        'polytecnic college courses',
    ],
    'education_overview': [
        'B Ed course details', 'B.Ed availability in College of Education',
        'Education college subject combinations', 'EGS Pillay Education College details',
    ],
    'naturopathy_overview': [
        'BNYS course details', 'BNYS eligibility and duration',
        'Naturopathy approvals', 'Yoga medical college course',
    ],
    'school_overview': [
        'School CBSE details', 'International School curriculum',
        'International School class range', 'School admission eligibility',
    ],
}

HELD_OUT_QUESTIONS = {
    'departments': 'Give me the full list of engineering branches.',
    'arts_science_overview': 'What degrees can I study at EGSPASC?',
    'pharmacy_overview': 'D Pharm B Pharm Pharm D and M Pharm duration sollu.',
    'nursing_overview': 'What training and recognition does the nursing college offer?',
    'polytechnic_overview': 'Which diploma streams are aided and self-financed?',
    'education_overview': 'What verified B.Ed information is available?',
    'naturopathy_overview': 'What do official records confirm about BNYS?',
    'school_overview': 'What is verified about EGS Pillay International School?',
}


def main():
    rows = [json.loads(line) for line in SOURCE.read_text(encoding='utf-8').splitlines() if line.strip()]
    grouped = {}
    for row in rows:
        college = row.get('college', 'engineering')
        grouped.setdefault(row['fact_id'], []).append({
            **row,
            'context': row['answer'],
            'college': college,
            'evidence_college': college,
        })

    train = []
    validation = []
    test = []
    positive_templates = (
        'What verified details are available about {topic} for {college}?',
        'Explain {topic} at {college} using this official record.',
        'Summarize the confirmed {topic} information for {college}.',
        '{college} oda {topic} details sollu.',
    )
    for fact_id, facts in grouped.items():
        exemplar = facts[0]
        train.extend(facts)
        topic = fact_id.replace('_', ' ')
        # Balance facts that have only one or two source phrasings so the model
        # does not learn rejection more strongly than valid non-engineering facts.
        for template in positive_templates:
            train.append({**exemplar, 'question': template.format(
                topic=topic, college=exemplar['college'])})
        for question in ANGLE_QUESTIONS.get(fact_id, []):
            train.append({**exemplar, 'question': question})
        validation.append({
            **exemplar,
            'question': f"Give the verified {topic} details for {exemplar['college']}.",
        })
        if fact_id in HELD_OUT_QUESTIONS:
            test.append({**exemplar, 'question': HELD_OUT_QUESTIONS[fact_id]})

    # Negative examples teach the model not to transfer a true fact from one
    # institution to another. These are evidence-mismatch controls, not reviews.
    colleges = sorted({row['college'] for rows in grouped.values() for row in rows})
    exemplars = [facts[0] for facts in grouped.values()]
    for index, wrong in enumerate(colleges):
        evidence = next((row for row in exemplars if row['college'] != wrong), None)
        if evidence is None:
            continue
        train.append({
            'question': f"Does this record verify the requested details for {wrong}?",
            'answer': FALLBACK,
            'context': evidence['answer'],
            'college': wrong,
            'evidence_college': evidence['college'],
            'fact_id': f"reject_{evidence['fact_id']}_{wrong}",
            'source_url': evidence['source_url'],
        })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, values in (('train', train), ('validation', validation), ('test', test)):
        (OUTPUT / f'{name}.jsonl').write_text(
            ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values),
            encoding='utf-8',
        )
    manifest = {
        'train': len(train),
        'validation': len(validation),
        'test': len(test),
        'positive_examples': len(train) - len(colleges),
        'negative_scope_examples': len(colleges),
        'multi_angle_examples': sum(map(len, ANGLE_QUESTIONS.values())),
        'private_data': False,
        'task': 'Grounded institution Q&A with cross-institution rejection',
    }
    (OUTPUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
