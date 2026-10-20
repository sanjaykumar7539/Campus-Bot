"""Create grounded, multi-angle student Q&A for every EGS Pillay institution.

Answers are copied only from the verified official-source dataset.  This file
adds realistic English, Tanglish and typo-heavy ways in which a prospective
student may ask; it never invents a new answer.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "training" / "online-college-qa" / "train.jsonl"
OUTPUT = ROOT / "training" / "all-institutions-student-journey"

COLLEGE_LABELS = {
    "engineering": "EGS Pillay Engineering College",
    "arts & science": "EGS Pillay Arts and Science College",
    "polytechnic": "EGS Pillay Polytechnic College",
    "pharmacy": "EGS Pillay College of Pharmacy",
    "nursing": "EGS Pillay College and School of Nursing",
    "education": "EGS Pillay College of Education",
    "naturopathy": "EGS Pillay Naturopathy and Yoga Medical College",
    "school": "EGS Pillay International School",
}

TOPIC_QUESTIONS = {
    "overview": ["Tell me everything a new student should know about {college}.", "{college} pathi full details sollunga."],
    "program": ["Which courses can I join at {college}?", "{college} la enna courses iruku?"],
    "admission": ["How can I join {college}?", "{college} join panna eligibility and documents enna?"],
    "contact": ["Whom should I contact for admission to {college}?", "{college} admission phone number and email sollu."],
    "facilities": ["Does {college} have hostel, bus, library and labs?", "{college} la hostel bus lab facilities iruka?"],
    "placement": ["What placement support and career scope does {college} offer?", "{college} placement and job scope epadi?"],
    "scholarship": ["What scholarships are available at {college}?", "{college} scholarship eligibility enna?"],
    "exam": ["Where can I check the exam timetable, syllabus and results for {college}?", "{college} exam result timetable enga check panrathu?"],
}

FACT_TOPIC = {
    "arts_science_overview": "program", "pharmacy_overview": "program",
    "nursing_overview": "program", "polytechnic_overview": "program",
    "education_overview": "program", "naturopathy_overview": "program",
    "school_overview": "overview", "departments": "program",
    "program_counts": "program", "nba_programs_scope": "program",
    "polytechnic_admission": "admission", "engineering_admission_tnea": "admission",
    "central_admissions_contact": "contact", "arts_science_admission_contact": "contact",
    "polytechnic_admission_contact": "contact", "pharmacy_admission_contact": "contact",
    "nursing_admission_contact": "contact", "polytechnic_facilities": "facilities",
    "arts_science_facilities": "facilities", "infrastructure": "facilities",
    "engineering_transport": "facilities", "placements": "placement",
    "placement_2025_26_departments": "placement", "engineering_scholarships": "scholarship",
    "examinations": "exam", "academic_documents": "exam",
}

TYPO_MAP = {
    "college": "collage", "admission": "admision", "eligibility": "eligiblity",
    "documents": "documnts", "facilities": "facilties", "pharmacy": "pharmasy",
    "nursing": "nurshing", "polytechnic": "polytecnic", "engineering": "enginering",
    "scholarship": "scholership", "placement": "placment", "details": "detials",
    "available": "availble", "infrastructure": "infrastucture",
}


def typo_variant(text: str) -> str:
    result = text
    for correct, typo in TYPO_MAP.items():
        result = re.sub(rf"\b{re.escape(correct)}\b", typo, result, flags=re.I)
    return result


def stable_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(" ".join(value.split()) for value in values if value.strip()))


def main() -> None:
    source_rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    facts: dict[str, dict] = {}
    source_questions: dict[str, list[str]] = {}
    for row in source_rows:
        facts.setdefault(row["fact_id"], row)
        source_questions.setdefault(row["fact_id"], []).append(row["question"])

    records = []
    for fact_id, fact in facts.items():
        college_key = fact.get("college", "engineering")
        college = COLLEGE_LABELS[college_key]
        topic = FACT_TOPIC.get(fact_id, "overview")
        readable_topic = fact_id.replace("_", " ")
        prompts = source_questions[fact_id] + [
            template.format(college=college) for template in TOPIC_QUESTIONS[topic]
        ] + [
            f"Give verified {readable_topic} details for {college}.",
            f"I am a new student. Explain {readable_topic} at {college} point by point.",
            f"{college} oda {readable_topic} details point wise ah sollu.",
            f"Please compare my options using the official {readable_topic} information for {college}.",
            f"Is the latest official {readable_topic} information available for {college}?",
        ]
        prompts = stable_unique(prompts)
        prompts += stable_unique([typo_variant(prompt) for prompt in prompts if typo_variant(prompt) != prompt])
        for question in stable_unique(prompts):
            language = "tanglish" if any(word in question.casefold() for word in (" enna", " iruku", " soll", " panna", " enga", " epadi", " oda ")) else "english"
            if question != typo_variant(question):
                language += "-typo"
            records.append({
                "question": question,
                "answer": fact["answer"],
                "context": fact["answer"],
                "source_url": fact["source_url"],
                "fact_id": fact_id,
                "college": college_key,
                "evidence_college": college_key,
                "language_style": language,
                "grounded": True,
            })

    random.Random(20261018).shuffle(records)
    splits = {"train": [], "validation": [], "test": []}
    for row in records:
        bucket = int(hashlib.sha256(row["question"].encode("utf-8")).hexdigest(), 16) % 10
        splits["test" if bucket == 0 else "validation" if bucket == 1 else "train"].append(row)

    # Keep the start of every training epoch institution-balanced. This matters
    # for bounded CPU fine-tunes where max_steps may stop well before a full
    # epoch and engineering otherwise dominates the early examples.
    buckets = {college: [] for college in COLLEGE_LABELS}
    for row in splits["train"]:
        buckets[row["college"]].append(row)
    balanced_train = []
    while any(buckets.values()):
        for college in COLLEGE_LABELS:
            if buckets[college]:
                balanced_train.append(buckets[college].pop())
    splits["train"] = balanced_train

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, rows in splits.items():
        (OUTPUT / f"{name}.jsonl").write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
        )

    manifest = {
        "total": len(records),
        "splits": {name: len(rows) for name, rows in splits.items()},
        "institutions": dict(Counter(row["college"] for row in records)),
        "language_styles": dict(Counter(row["language_style"] for row in records)),
        "verified_fact_ids": len(facts),
        "answer_policy": "Answers copied from official-source verified facts; no synthetic claims.",
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
