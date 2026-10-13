import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.core.retriever import Retriever


def main():
    dataset_path = os.path.join(ROOT, "evaluation", "questions.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    retriever = Retriever()
    evaluated = 0
    source_hits = 0
    print("\n=== Retrieval Evaluation ===\n")
    for idx, case in enumerate(cases, 1):
        docs, scores = retriever.retrieve(case["question"])
        sources = [d.metadata.get("doc_name", "Unknown") for d in docs]
        expected = case.get("expected_source", "").strip().lower()
        hit = None
        if expected:
            evaluated += 1
            hit = any(expected in s.lower() for s in sources)
            source_hits += int(hit)
        print(f"{idx}. {case['question']}")
        print(f"   Retrieved: {list(zip(sources, [round(s, 3) for s in scores]))}")
        print(f"   Expected-source hit: {hit if expected else 'SKIPPED (not configured)'}\n")

    if evaluated:
        print(f"Source Recall@K: {source_hits}/{evaluated} = {source_hits/evaluated:.1%}")
    else:
        print("No expected sources configured yet. Edit evaluation/questions.json first.")


if __name__ == "__main__":
    main()
