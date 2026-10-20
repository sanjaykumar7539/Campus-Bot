# Student, developer and reviewer audit — 20 October 2026

The current chat flow handles known institution questions well, but is not ready
to reliably advise a new student asking unfamiliar or compound questions.

## Results and scope

| Perspective | Requirement checks passed | Main result |
| --- | ---: | --- |
| New student | 15/17 | Eight institution overviews work; a sports follow-up loses context and an Arts acknowledgement names Engineering. |
| Developer/tester | 7/7 | Selected typo cases, SSE reconstruction, input validation and a separate-session question pass their content/HTTP checks. |
| Independent reviewer perspective | 3/10 | Missing fee information and cross-institution NBA claims are handled conservatively; counselling, compound questions and language output fail. |
| Total after manual review | 25/34 | Nine demonstrated requirement failures remain. |

The original automated result was 24/34. Manual inspection accepted the negative
feedback answer: it explicitly explains that no audited aggregate rating or
representative review summary is available. Its regex was too narrow. The
original results are preserved in `results.json`; the adjudication is recorded
in `review.json`. These are requirement checks, not a factual-accuracy score.

Separately, HTTP rate limiting passed (first request 200, second 429), and 55
existing regression tests passed across context, question normalization,
language helpers, security, contact-source checks and student-life answers.

The audit used the real in-process chat API, an isolated SQLite database, the
existing local index, and offline model files. It did not run the startup
lifespan, public deployment, browser UI, concurrent-load tests, a live website
verification, or the fine-tuned adapter. Production application code was not
changed during this audit.

## Demonstrated failures

| Priority | Question or conversation | Actual behavior | Required behavior |
| --- | --- | --- | --- |
| High | “I am a new student and want to join this college. Help me choose a course.” | Returns a sentence from a chairman message about student success. | Ask qualification/subjects, interests and budget; identify the institution; give a relevant next step. |
| High | “How can I join EGSPEC, what documents are needed, and what scholarships are available?” | Returns promotional copy, a tag and privacy-policy text about California/Florida. | Address admission, documents and scholarships separately; distinguish verified details from missing information. |
| High | “Does studying CSE guarantee a job?” | Returns historical accreditation content and privacy/employment boilerplate. | Explain that a degree does not guarantee employment, then discuss relevant career preparation. |
| High | “My TNEA cutoff is 150. Will I definitely get CSE in EGSPEC in 2027?” | Returns promotional content and a flattened navigation/statistics block. | Explain that admission cannot be guaranteed; request category/quota and use year-specific official counselling data before estimating a chance. |
| High | “Tell me about EGSPEC”, language=`ta` | English answer with Tamil language metadata. | Produce Tamil content, not only a language label. |
| High | “college la sports enna iruku”, language=`tanglish` | English answer. | Produce understandable Tanglish while preserving factual names and numbers. |
| Medium | “sports” → “which season?” | Loses the sports topic and returns the admissions fallback. | Use the prior sports context and explain that a fixed recurring season is not established in the records. |
| Medium | Arts overview → “ok super” | Acknowledgement says “E.G.S. Pillay Engineering College”. | Use neutral wording or the current institution. The following hostel question does retain Arts context. |
| Medium | Arts overview | Displays `Sources:` and raw URLs inside answer text. | Respect the requested UI behavior while keeping provenance internally. |

The negative-feedback answer was acceptable: it avoided treating testimonials
as representative evidence and recommended balanced evaluation. A policy of
showing only positive information would fail this reviewer standard.

## Timing

Of 32 HTTP-200 responses, 26 completed within 3 seconds in this test process.
The median was about 51 ms. The first retrieval-dependent sports follow-up took
73.19 seconds; a later Pharmacy accreditation question took 64.09 seconds.
Other retrieval cases took approximately 7.52–16.46 seconds.

These timings include local lazy initialization where applicable. They do not
establish deployed performance. Startup warm-up can move initialization out of
the first question, but these observations do not substantiate a universal
1–3 second response promise.

## Root causes and recommended implementation order

1. Add a student-advice intent that gathers the missing decision inputs and
   handles several requested topics. The current fuzzy fact lookup and
   extractive retrieval can return a thematically related paragraph without
   answering the question.
2. Reject privacy/legal/navigation fragments during ingestion and answer
   assembly. Verify relevance to each requested topic before marking a reply
   grounded; presence in a source alone is insufficient.
3. Apply actual language rendering to the final answer. `src/api/routes.py`
   currently resolves the requested language and returns its label, but does
   not translate the result.
4. Extend bounded context handling to short time/season follow-ups and make
   acknowledgements institution-neutral.
5. Remove source footer lines at the final display boundary while retaining
   the audit provenance.
6. Profile retrieval, reranking and retry costs with startup warm-up enabled.
   Measure user-visible answer latency separately from initial SSE status.

The API currently calls the verified RAG chain. Passing adapter training or
generation tests does not establish that this API is using that adapter.
Routing and answer-selection failures need their own fixes and regression
tests.

## Example of the intended first reply to a new student

> Vanakkam! College/course choose panna help panren.
>
> - Neenga 10th, 12th, diploma, illa degree mudichirukeengala? 12th-na endha subjects?
> - Engineering, Arts & Science, Pharmacy, Nursing, Polytechnic—edhula interest? Theriyalana pidicha subjects sollunga.
> - Unga marks/cutoff, yearly budget, hostel illa daily bus requirement sollunga.
> - Adhai base panni suitable courses, career options, eligibility, admission steps, available scholarships and facilities-a point-wise explain panren.
> - Exact fee, current seat availability or admission chance-ku verified course/year details thevai.

This is a proposed counselling response, not the current system's output.
Ask a few relevant questions, then build on the answers rather than repeating
the full institution overview at every turn.

## Reproduce

Run `python scripts/audit_student_experience.py` from the project virtual
environment. The audit writes to this report directory and uses its own
database. Its future negative-feedback check accepts the vocabulary observed
in the manually reviewed response; the original raw result remains unchanged.

Read `results.json` for all 34 questions, complete answers, checks and timings,
and `review.json` for the manual adjudication and final requirement counts.
