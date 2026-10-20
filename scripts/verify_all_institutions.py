"""Run a multi-angle production RAG audit and write verification documents."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.rag_chain import RAGChain


CASES = {
    "Engineering": [
        ("Engineering departments", "departments"),
        ("Which courses are NBA accredited and what is their scope?", "nba_programs_scope"),
        ("What is the NIRF 2025 rank band?", "nirf_2025"),
        ("Which departments have recognized research centers?", "research_centers"),
        ("Examinations", "examinations"),
    ],
    "Arts & Science": [
        ("Arts science departments", "arts_science_overview"),
        ("Arts Science UG PG programs", "arts_science_overview"),
        ("Arts Science research programs", "arts_science_overview"),
        ("EGS Pillay Arts Science courses", "arts_science_overview"),
    ],
    "Pharmacy": [
        ("Pharmacy courses enna?", "pharmacy_overview"),
        ("Pharmacy duration and intake", "pharmacy_overview"),
        ("Pharmacy eligibility details", "pharmacy_overview"),
        ("M Pharm branches", "pharmacy_overview"),
        ("parmachy college details sollu", "pharmacy_overview"),
    ],
    "Nursing": [
        ("B sc nursing DGNM details", "nursing_overview"),
        ("Nursing facilities and clinical training", "nursing_overview"),
        ("Is Nursing INC recognized?", "nursing_overview"),
        ("Nursing placement assistance", "nursing_overview"),
        ("nurshibg courses enna", "nursing_overview"),
    ],
    "Polytechnic": [
        ("Polytechnic branches", "polytechnic_overview"),
        ("Polytechnic aided and self financing branches", "polytechnic_overview"),
        ("Polytechnic DOTE approval", "polytechnic_overview"),
        ("Diploma duration in Polytechnic", "polytechnic_overview"),
        ("polytecnic college courses", "polytechnic_overview"),
    ],
    "College of Education": [
        ("B Ed course details", "education_overview"),
        ("B.Ed availability in College of Education", "education_overview"),
        ("Education college subject combinations", "education_overview"),
        ("EGS Pillay Education College details", "education_overview"),
    ],
    "Naturopathy & Yoga": [
        ("BNYS course details", "naturopathy_overview"),
        ("BNYS eligibility and duration", "naturopathy_overview"),
        ("Naturopathy approvals", "naturopathy_overview"),
        ("Yoga medical college course", "naturopathy_overview"),
    ],
    "International School": [
        ("School CBSE details", "school_overview"),
        ("International School curriculum", "school_overview"),
        ("International School class range", "school_overview"),
        ("School admission eligibility", "school_overview"),
    ],
}


def main() -> int:
    rag = RAGChain()
    rows = []
    for institution, cases in CASES.items():
        for question, expected_fact in cases:
            started = time.perf_counter()
            result = rag.invoke(question)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            actual_fact = result.get("fact_id")
            passed = bool(result.get("is_grounded")) and actual_fact == expected_fact
            rows.append({
                "institution": institution,
                "question": question,
                "expected_fact": expected_fact,
                "actual_fact": actual_fact,
                "grounded": bool(result.get("is_grounded")),
                "passed": passed,
                "response_ms": elapsed_ms,
                "source": (result.get("sources") or [{}])[0].get("document", ""),
                "answer": result.get("answer", ""),
            })

    report_dir = ROOT / "reports"
    report_dir.mkdir(exist_ok=True)
    generated = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {"generated_at": generated, "passed": sum(r["passed"] for r in rows),
               "total": len(rows), "results": rows}
    (report_dir / "all-institutions-verification.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# All Institutions Verification Report", "",
        f"Generated: `{generated}`", "",
        f"Result: **{payload['passed']}/{payload['total']} passed**", "",
        "Every passing answer was grounded in the expected institution-owned verified fact.", "",
    ]
    for institution in CASES:
        lines.extend([f"## {institution}", "", "| Question | Fact | Grounded | Time | Source |", "|---|---|---:|---:|---|"])
        for row in (item for item in rows if item["institution"] == institution):
            source = row["source"] or "—"
            lines.append(
                f"| {row['question']} | `{row['actual_fact'] or 'none'}` | "
                f"{'PASS' if row['passed'] else 'FAIL'} | {row['response_ms']} ms | {source} |"
            )
        lines.append("")
    (report_dir / "all-institutions-verification.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"All-institution verification: {payload['passed']}/{payload['total']} passed")
    return 0 if payload["passed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
