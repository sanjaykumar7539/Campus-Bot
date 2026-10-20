"""Exercise the actual chat API from student, developer and reviewer perspectives.

Uses a separate SQLite database and the existing local knowledge index. No crawl,
training, model activation, production chat writes, or external translation occurs.
Checks measure explicit requirements, not independent factual accuracy.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT_DIR = Path(os.environ.get("CAMPUS_AUDIT_REPORT_DIR",
                                str(ROOT / "reports" / "student-experience-20261020")))
REPORT_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{REPORT_DIR / 'audit.sqlite3'}"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["NETWORK_MODE"] = "offline"

from fastapi.testclient import TestClient
from src.api.main import app
from src.api import routes
from src.api.rate_limiter import SlidingWindowRateLimiter


def case(role, name, question, *, session=None, patterns=(), forbidden=(),
         status=200, language="en", stream=False):
    return dict(role=role, name=name, question=question, session=session or name,
                patterns=list(patterns), forbidden=list(forbidden), status=status,
                language=language, stream=stream)


CASES = [
    case("student", "engineering-overview", "Tell me about EGSPEC",
         patterns=[r"1995", r"11 undergraduate", r"Computer Science", r"scope"]),
    case("student", "arts-overview", "Tell me about EGS Pillay Arts and Science College",
         session="arts-journey", patterns=[r"Arts", r"BCA", r"scope"]),
    case("student", "arts-thanks", "ok super", session="arts-journey",
         patterns=[r"welcome"], forbidden=[r"Engineering College"]),
    case("student", "arts-hostel-followup", "what about hostel?", session="arts-journey",
         patterns=[r"hostel", r"Arts"], forbidden=[r"Engineering College"]),
    case("student", "pharmacy-overview", "Tell me about EGS Pillay Pharmacy",
         session="pharmacy-journey", patterns=[r"B.Pharm", r"Pharm.D", r"scope"]),
    case("student", "pharmacy-fees-followup", "what about its fees?", session="pharmacy-journey",
         patterns=[r"Pharmacy", r"cannot verify|could not verify|not verified|not.*available"]),
    case("student", "nursing-overview", "Tell me about EGS Pillay Nursing",
         patterns=[r"B.Sc", r"DGNM", r"scope"]),
    case("student", "polytechnic-overview", "Tell me about EGS Pillay Polytechnic",
         patterns=[r"diploma", r"Mechanical", r"scope"]),
    case("student", "education-overview", "Tell me about EGS Pillay College of Education",
         patterns=[r"B.Ed", r"scope"]),
    case("student", "naturopathy-overview", "Tell me about EGS Pillay Naturopathy",
         patterns=[r"BNYS", r"not verified|not established|unavailable"]),
    case("student", "school-overview", "Tell me about EGS Pillay International School",
         patterns=[r"CBSE", r"class range"]),
    case("student", "admission", "How to join EGSPEC through TNEA?",
         patterns=[r"TNEA", r"3806"]),
    case("student", "placement", "Give engineering placement highest package, placement percentage, recruiters and offers",
         patterns=[r"placement", r"recruit|compan", r"LPA|package"]),
    case("student", "transport", "EGSPEC transport routes",
         session="transport-journey", patterns=[r"Sirkali", r"route"]),
    case("student", "transport-followup", "and Sirkali timing?", session="transport-journey",
         patterns=[r"Sirkali", r"7:10", r"pickup|stop"]),
    case("student", "sports", "sports", session="sports-journey",
         patterns=[r"cricket", r"basketball"]),
    case("student", "sports-followup", "which season?", session="sports-journey",
         patterns=[r"no verified fixed|not established"]),
    case("developer", "typo-admission", "enginering collage la TNEA moolama epadi join pandrathu cutoff fixed ah",
         patterns=[r"TNEA", r"cutoff"]),
    case("developer", "typo-pharmacy", "parmachy college details sollu",
         patterns=[r"B.Pharm", r"D.Pharm"], forbidden=[r"Mechanical"]),
    case("developer", "typo-nursing", "nurshibg courses enna",
         patterns=[r"Nursing", r"DGNM"], forbidden=[r"TNEA"]),
    case("developer", "stream-answer", "Departments", stream=True,
         patterns=[r"Computer Science", r"Mechanical"]),
    case("developer", "invalid-empty", "", status=422),
    case("developer", "invalid-too-long", "x" * 1001, status=422),
    case("developer", "session-isolation", "what about its fees?",
         patterns=[r"which|course|college|not.*verified|do not have"]),
    case("reviewer", "pharmacy-no-engineering-nba", "Is Pharmacy NBA accredited?",
         forbidden=[r"CSE.*ECE", r"eight NBA", r"30 June 2028"]),
    case("reviewer", "unknown-school-fees", "What is the exact International School fee for 2027?",
         patterns=[r"not.*verified|do not have|not.*publish|cannot verify|could not verify|not established"],
         forbidden=[r"₹\s*\d"]),
    case("reviewer", "no-guaranteed-job", "Does studying CSE guarantee a job?",
         patterns=[r"not guaranteed|no guarantee|does not guarantee|cannot guarantee|not.*job guarantee"]),
    case("reviewer", "negative-feedback", "anything negative feedback about this college",
         patterns=[r"review|feedback", r"verif|independent|audited|representative"]),
    case("reviewer", "fresh-student-advice", "I am a new student and want to join this college. Help me choose a course.",
         patterns=[r"interest|prefer", r"qualification|12th|subjects|marks|budget"]),
    case("reviewer", "compound-admission", "How can I join EGSPEC, what documents are needed, and what scholarships are available?",
         patterns=[r"TNEA|admission", r"document|certificate", r"scholarship"]),
    case("reviewer", "cutoff-guarantee", "My TNEA cutoff is 150. Will I definitely get CSE in EGSPEC in 2027?",
         patterns=[r"cannot guarantee|not guarantee|not fixed|depends|cannot.*confirm|not.*verified"],
         forbidden=[r"you will definitely|guaranteed admission"]),
    case("reviewer", "tamil-output", "Tell me about EGSPEC", language="ta",
         patterns=[r"[\u0b80-\u0bff]"]),
    case("reviewer", "tanglish-output", "college la sports enna iruku", language="tanglish",
         patterns=[r"\b(?:iruk|pann|soll|unga|indha|anga|kku)\w*\b"]),
    case("reviewer", "hide-source-lines", "Tell me about EGS Pillay Arts and Science College",
         forbidden=[r"https?://", r"\bSources?:"]),
]

if os.environ.get("CAMPUS_AUDIT_EXTENDED") == "1":
    institution_names = [
        "EGSPEC", "EGS Pillay Arts and Science College", "EGS Pillay Pharmacy",
        "EGS Pillay Nursing", "EGS Pillay Polytechnic", "EGS Pillay College of Education",
        "EGS Pillay Naturopathy", "EGS Pillay International School",
    ]
    for index, institution in enumerate(institution_names):
        for locale in ("ta", "tanglish"):
            CASES.append(case(
                "extended", f"locale-{index}-{locale}", f"Tell me about {institution}",
                language=locale,
                patterns=[r"[\u0b80-\u0bff]"] if locale == "ta" else [r"\b(?:iruk|pann|thevai|aagala|poruth)\w*\b"],
                forbidden=[r"https?://"],
            ))
    CASES.extend([
        case("extended", "new-student-variation", "I finished 12th. Help me select a suitable course",
             patterns=[r"qualification", r"interests", r"budget"]),
        case("extended", "nursing-job-variation", "Will a nursing degree definitely get me a job?",
             patterns=[r"does not guarantee a job"]),
        case("extended", "admission-variation", "What scholarships and certificates do I need to apply to EGSPEC?",
             patterns=[r"Admissions", r"Documents", r"Scholarships", r"3806"]),
        case("extended", "nursing-fees-tamil", "What are the nursing tuition fees for 2027?",
             language="ta", patterns=[r"உறுதிப்படுத்தப்படவில்லை"], forbidden=[r"₹\s*\d"]),
        case("extended", "tnea-tanglish", "How to join EGSPEC through TNEA?",
             language="tanglish", patterns=[r"3806", r"pannanum"]),
    ])


def main():
    # Keep the real limiter and use separate test sessions; test its boundary below.
    routes.chat_rate_limiter = SlidingWindowRateLimiter(1000, 60)
    client = TestClient(app)  # Deliberately no lifespan/crawl; lazy local retrieval is real.
    report = {
        "generated_at": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
        "scope": "in-process actual API, local verified facts and local retrieval",
        "limitations": [
            "No browser, public deployment, concurrent load, or live website audit.",
            "Requirement checks are not a comprehensive factual-accuracy score.",
            "The chat API uses verified RAG; this does not evaluate the new adapter.",
            "Tests use an isolated database, offline models, and an increased audit rate limit.",
        ],
        "results": [],
    }
    report_path = REPORT_DIR / "results.json"
    for item in CASES:
        started = time.perf_counter()
        error = None
        body = {}
        events = []
        status = None
        try:
            response = client.post(
                "/api/v1/chat/stream" if item["stream"] else "/api/v1/chat",
                json={"session_id": "audit-" + item["session"],
                      "message": item["question"], "language": item["language"]},
            )
            status = response.status_code
            if item["stream"]:
                current = None
                for line in response.text.splitlines():
                    if line.startswith("event: "):
                        current = line[7:]
                    elif line.startswith("data: "):
                        events.append({"event": current, "data": json.loads(line[6:])})
                body = next((event["data"] for event in events if event["event"] == "complete"), {})
            else:
                body = response.json()
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        answer = body.get("answer", "")
        checks = {"status": status == item["status"], "no_exception": error is None}
        if item["status"] == 200:
            checks["nonempty_answer"] = bool(answer.strip())
            for pattern in item["patterns"]:
                checks["required:" + pattern] = bool(re.search(pattern, answer, re.I))
            for pattern in item["forbidden"]:
                checks["forbidden:" + pattern] = not bool(re.search(pattern, answer, re.I))
            if item["language"] in {"ta", "tanglish"}:
                checks["actual_output_language"] = body.get("language") == item["language"]
        if item["stream"]:
            checks["stream_complete"] = bool(body)
            checks["stream_integrity"] = "".join(
                event["data"]["text"] for event in events if event["event"] == "token"
            ) == answer
        record = {**item, "actual_status": status, "answer": answer,
                  "reported_language": body.get("language"),
                  "grounded": body.get("is_grounded"), "response_ms": elapsed,
                  "checks": checks, "passed": all(checks.values()), "error": error}
        report["results"].append(record)
        report["total"] = len(report["results"])
        report["passed"] = sum(row["passed"] for row in report["results"])
        report["failed"] = report["total"] - report["passed"]
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        failures = [key for key, value in checks.items() if not value]
        print(f"{'PASS' if record['passed'] else 'FAIL'} {item['name']} "
              f"{elapsed}ms {failures}", flush=True)

    # Real HTTP rate-limit behavior, independent of the content checks above.
    routes.chat_rate_limiter = SlidingWindowRateLimiter(1, 60)
    payload = {"session_id": "audit-rate-limit", "message": "egspec"}
    first = client.post("/api/v1/chat", json=payload)
    second = client.post("/api/v1/chat", json=payload)
    report["rate_limit"] = {"first": first.status_code, "second": second.status_code,
                            "passed": first.status_code == 200 and second.status_code == 429}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report: {report_path}", flush=True)
    return 0 if not report["failed"] and report["rate_limit"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
