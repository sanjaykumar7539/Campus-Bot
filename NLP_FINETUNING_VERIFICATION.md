# Grounded NLP fine-tuning verification

Completed 13 October 2026 on CPU. The adapter is saved at
`.venv/models/smollm2-grounded-nlp-20261013` and remains inactive.

## Training

- Base: local SmolLM2-360M-Instruct, with a new LoRA adapter.
- 49 examples; two epochs; 98 gradient updates.
- Four CPU threads, float32, maximum sequence length 384.
- Only assistant answer tokens contribute to Q&A training loss.
- Six validation questions and six reserved final-test questions.
- Answer-only validation loss: 0.1681552835 before, 0.0701126602 after.
- English natural-language paraphrases and college-ownership fallback cases.

Evidence: `.venv/models/smollm2-grounded-nlp-20261013/training_metrics.json`.

## Answer accuracy on a 0-to-1 scale

Accuracy is the number of factually correct answers divided by questions
evaluated. Equivalent wording is accepted during review. Incorrect ownership
of an otherwise true fact counts as an incorrect answer.

| Measurement | Base model | Trained adapter |
| --- | --- | --- |
| Reviewed answer accuracy | 4/6 = 0.6667 | 4/6 = 0.6667 |
| Matching-evidence factual questions | 4/4 = 1.00 | 4/4 = 1.00 |
| Cross-college fallback questions | 0/2 = 0.00 | 0/2 = 0.00 |
| Exact reference wording | 2/6 = 0.3333 | 2/6 = 0.3333 |

The four factual responses correctly answered unseen English phrasings about
the college name, establishment year, autonomous status, and program counts
using supplied evidence. Two answers incorrectly reused the engineering
college's establishment year when the requested college was pharmacy or nursing.

This fine-tuning run did **not demonstrate an answer-accuracy gain** over
the base model. Its lower loss does not compensate for failed college isolation.
The adapter is **not approved for automatic factual answer generation**.
Keep the application-level college scope filter and verified-answer fallback.

Raw evidence and reviewed labels:

- [Base-model test](training/grounded-nlp/base-test.json)
- [Adapter test](training/grounded-nlp/adapter-test.json)
- [Dataset manifest](training/grounded-nlp/manifest.json)

## What this evaluation establishes

The final-test question strings were absent from both training and validation.
The underlying facts and evidence appear in training, so the score measures
these English phrasings with evidence, not unknown facts or broad NLP capability.
Six questions are too few to establish production accuracy. There is no Tamil,
Tanglish, speech, or general multilingual model accuracy measurement in this run.

These are evidence-grounded prompts. The earlier closed-book score of 0.00
used different test questions without supplied evidence; it is not a valid
before/after comparison with this 0.6667 result. The history records have not
been freshly verified against the official website; see source limitations in
`TRAINING_VERIFICATION.md`. Correctness here means consistency with supplied
reference records, not an independent certification that those records are current.

## Code verification

26 focused tests passed for grounding prompts, disjoint question phrasing,
accuracy scoring, college-scope isolation, and existing verified natural-language
answer matching. Finite adapter tensors and completed training metrics were
also checked by the inference verification script.

Reproduction commands are in the evidence-grounded NLP section of `TRAINING.md`.
