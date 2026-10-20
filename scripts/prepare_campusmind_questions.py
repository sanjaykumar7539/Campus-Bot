"""Convert the supplied CampusMind DOCX question bank into an eval JSONL."""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from docx import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.campus_operational_answers import operational_answer
from src.core.question_understanding import normalize_question


def to_english(question: str) -> str:
    """Convert the recurring Tamil-English templates into clean English."""
    text = question.strip()
    rules = (
        (r'^Naalaiku (.+?) ku (.+?) irukka\?$', r'Is \2 scheduled for \1 tomorrow?'),
        (r'^(.+?) students-ku (.+?) eppo\?$', r'When is \2 scheduled for \1 students?'),
        (r'^(.+?) block-la (.+?) irukka\?$', r'Is \2 available in the \1 block?'),
        (r'^(today|tomorrow|morning|afternoon|evening) (.+?) open aagirukkuma\?$', r'Is \2 open \1?'),
        (r'^(.+?) attend panna allow pannuvangala\?$', r'Are students allowed to attend \1?'),
        (r'^(.+?) vaanga evlo naal aagum\?$', r'How long does it take to obtain \1?'),
        (r'^(.+?) kitta sign vaanga enga poga num\?$', r'Where should I go to get the \1 signature?'),
        (r'^(.+?) address or contact details kedaikuma\?$', r'Can I get the address or contact details of the \1?'),
        (r'^(.+?) lab-ku enna software thevai\?$', r'What software is required for the \1 lab?'),
        (r'^(.+?) tholanjiduchu, duplicate epdi vaangarathu\?$', r'I lost my \1. How can I obtain a duplicate?'),
        (r'^(.+?) submit panna last date eppo\?$', r'What is the deadline for submitting the \1?'),
        (r'^(.+?) enga kedaikkum\?$', r'Where can I get the \1?'),
    )
    for pattern, replacement in rules:
        updated = re.sub(pattern, replacement, text, flags=re.I)
        if updated != text:
            return updated
    replacements = {
        'enga': 'where', 'eppo': 'when', 'epdi': 'how', 'enna': 'what',
        'irukka': 'available', 'kedaikkum': 'available', 'evlo': 'how much',
    }
    return re.sub(
        r'\b(?:enga|eppo|epdi|enna|irukka|kedaikkum|evlo)\b',
        lambda match: replacements[match.group(0).casefold()], text, flags=re.I,
    )


def typo_variant(question: str) -> str:
    substitutions = (
        ('tomorrow', 'tomorow'), ('available', 'availble'),
        ('department', 'departmant'), ('students', 'studnts'),
        ('certificate', 'certficate'), ('library', 'libary'),
        ('placement', 'placemant'), ('examination', 'examnation'),
        ('syllabus', 'sylabus'), ('scholarship', 'scholorship'),
        ('details', 'detials'), ('college', 'collage'),
    )
    for correct, typo in substitutions:
        changed = re.sub(rf'\b{correct}\b', typo, question, count=1, flags=re.I)
        if changed != question:
            return changed
    changed = re.sub(r'\bthe\b', 'teh', question, count=1, flags=re.I)
    # Every row gets a harmless, recoverable keyboard-style variation.
    return changed if changed != question else f'plese {question}'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('docx', type=Path)
    parser.add_argument('--output', type=Path, default=Path('training/campusmind-2000-evaluation.jsonl'))
    parser.add_argument('--language-dir', type=Path, default=Path('training/campusmind-language-qa'))
    args = parser.parse_args()

    questions = []
    for paragraph in Document(args.docx).paragraphs:
        text = re.sub(r'^\s*\d+\.\s*', '', paragraph.text).strip()
        if text and not text.startswith('CampusMind RAG Dataset') and not text.startswith('This document'):
            questions.append(text)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    with args.output.open('w', encoding='utf-8') as stream:
        for index, question in enumerate(questions, 1):
            normalized = normalize_question(question)
            match = operational_answer(normalized)
            intent = match['fact_id'] if match else 'rag_lookup'
            counts[intent] += 1
            stream.write(json.dumps({
                'id': index,
                'question': question,
                'normalized_question': normalized,
                'expected_route': intent,
            }, ensure_ascii=False) + '\n')

    args.language_dir.mkdir(parents=True, exist_ok=True)
    english_rows = []
    qa_rows = []
    for index, question in enumerate(questions, 1):
        english = to_english(question)
        match = operational_answer(english)
        if not match:
            raise RuntimeError(f'English conversion lost its route at question {index}: {english}')
        english_rows.append({'id': index, 'question': english, 'source_question': question})
        qa_rows.extend((
            {'question': question, 'answer': operational_answer(question)['answer'], 'language': 'source'},
            {'question': english, 'answer': match['answer'], 'language': 'en'},
            {'question': typo_variant(english), 'answer': match['answer'], 'language': 'en-typo'},
        ))

    with (args.language_dir / 'english_questions.jsonl').open('w', encoding='utf-8') as stream:
        for row in english_rows:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    with (args.language_dir / 'train.jsonl').open('w', encoding='utf-8') as train, \
            (args.language_dir / 'validation.jsonl').open('w', encoding='utf-8') as validation:
        for index, row in enumerate(qa_rows):
            target = validation if index % 10 == 0 else train
            target.write(json.dumps(row, ensure_ascii=False) + '\n')

    print(json.dumps({
        'questions': len(questions), 'english_questions': len(english_rows),
        'qa_examples': len(qa_rows), 'routes': counts,
    }, default=dict, indent=2))


if __name__ == '__main__':
    main()
