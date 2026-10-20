"""Verify simple, complex and confusing student questions for every institution."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.rag_chain import RAGChain

REPORT = ROOT / "reports" / "student-question-matrix-20261018.json"

CASES = [
    # Engineering
    ("engineering", "simple", "Tell me about EGSPEC", "engineering_overview", ["11 undergraduate", "NAAC A++"]),
    ("engineering", "complex", "Give engineering placement highest package, placement percentage, recruiters and offers", "placements", ["60 LPA", "95.8%", "1,400+"]),
    ("engineering", "confusing", "enginering collage la TNEA moolama epadi join pandrathu cutoff fixed ah", "engineering_admission_tnea", ["3806", "cutoff"]),
    # Arts and Science
    ("arts & science", "simple", "What courses are in EGS Pillay Arts and Science College?", "arts_science_overview", ["B.Com", "B.Sc"]),
    ("arts & science", "complex", "Arts and Science college hostel library internet computer lab details", "arts_science_facilities", ["30,000", "1 Gbps"]),
    ("arts & science", "confusing", "arts clg admision ku yaruku call pannanum mail enna", "arts_science_admission_contact", ["98765 43210"]),
    # Pharmacy
    ("pharmacy", "simple", "Pharmacy college courses enna?", "pharmacy_overview", ["D.Pharm", "B.Pharm"]),
    ("pharmacy", "complex", "Explain D Pharm B Pharm Pharm D M Pharm duration intake branches and job scope", "pharmacy_overview", ["6 years", "Pharmaceutics"]),
    ("pharmacy", "confusing", "pharmasy admision ku contact numbr and mail sollu", "pharmacy_admission_contact", ["99887 76655"]),
    # Nursing
    ("nursing", "simple", "What nursing courses are available?", "nursing_overview", ["B.Sc", "DGNM"]),
    ("nursing", "complex", "Does Nursing have INC recognition clinical training labs and placement assistance?", "nursing_overview", ["INC", "clinical"]),
    ("nursing", "confusing", "nurshing join panna yaruku call pannanum eligibility age fee hum kekanum", "nursing_admission_contact", ["99768 88999"]),
    # Polytechnic
    ("polytechnic", "simple", "List Polytechnic diploma branches", "polytechnic_overview", ["Computer Engineering", "Mechanical"]),
    ("polytechnic", "complex", "After 10th can I join Polytechnic and what duration documents and percentage are needed?", "polytechnic_admission", ["35%", "SSLC"]),
    ("polytechnic", "confusing", "polytecnic la boys girls hostal bus wifi workshop la iruka", "polytechnic_facilities", ["boys", "Wi-Fi"]),
    # Education
    ("education", "simple", "Tell me about EGS Pillay College of Education", "education_overview", ["B.Ed", "100"]),
    ("education", "complex", "Is B.Ed NCTE approved, which university is it affiliated to, intake and college code?", "education_overview", ["NCTE", "11316"]),
    ("education", "confusing", "education collage b ed ku ethana seat contact enna", "education_overview", ["100", "252113"]),
    # Naturopathy
    ("naturopathy", "simple", "Which course is offered by EGS Pillay Naturopathy College?", "naturopathy_overview", ["Bachelor of Naturopathy"]),
    ("naturopathy", "complex", "Explain BNYS duration intake eligibility approval facilities and fees", "naturopathy_overview", ["Bachelor of Naturopathy", "not stated"]),
    ("naturopathy", "confusing", "yoga medical collage la enna course join panna mudiyum details sollu", "naturopathy_overview", ["Bachelor of Naturopathy"]),
    # International School
    ("school", "simple", "Tell me about EGS Pillay International School", "school_overview", ["CBSE"]),
    ("school", "complex", "What curriculum, class range, fees and grade eligibility does the International School have?", "school_overview", ["CBSE", "do not publish"]),
    ("school", "confusing", "international schol CBSE ah which class varaikum admision edukuranga", "school_overview", ["CBSE", "class range"]),
]


def main() -> None:
    chain = RAGChain()
    results = []
    for institution, level, question, expected_fact, markers in CASES:
        response = chain.invoke(question)
        answer = response.get("answer", "")
        passed = (
            response.get("is_grounded") is True
            and response.get("fact_id") == expected_fact
            and all(marker.casefold() in answer.casefold() for marker in markers)
        )
        record = {
            "institution": institution, "level": level, "question": question,
            "expected_fact_id": expected_fact, "actual_fact_id": response.get("fact_id"),
            "expected_markers": markers, "grounded": response.get("is_grounded"),
            "passed": passed, "answer": answer,
        }
        results.append(record)
        print(f"{'PASS' if passed else 'FAIL'} | {institution:15} | {level:9} | {response.get('fact_id')}")

    summary = {
        "total": len(results), "passed": sum(row["passed"] for row in results),
        "failed": sum(not row["passed"] for row in results), "results": results,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("total", "passed", "failed")}))
    raise SystemExit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
