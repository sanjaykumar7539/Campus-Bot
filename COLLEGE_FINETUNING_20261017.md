# College fine-tuning verification — 17 October 2026

## Outcome

CPU fine-tuning completed: 88 updates on 88 examples.
New adapter: .venv/models/smollm2-college-scope-20261017.

On the same eight held-out prompts, reviewed accuracy changed from
**4/8 (0.50) to 5/8 (0.625)**. Cross-college fallback improved, but correct
answers with matching evidence regressed. The adapter is **not approved
for activation**. Keep the application college-scope rules.

## Training

- Base: local SmolLM2-360M-Instruct.
- Starting adapter: smollm2-grounded-nlp-20261013.
- CPU float32, four threads, one shuffled epoch, seed 42.
- Answer-only LoRA loss, maximum sequence length 384.
- Learning rate: 0.0002; fresh optimizer state.
- 88 examples, including 42 cross-college mismatch examples.
- Six validation examples and eight final-test questions.
- English and selected Tanglish phrasings; no Tamil model accuracy claim.
- Validation loss: 0.0701126602 before, 0.0078330356 after.
- Dataset hashes and settings are stored in training_metrics.json in the
  new adapter directory. Base weights and earlier adapters are preserved.

## Answer verification

Both adapters used identical evidence-grounded prompts with deterministic
decoding and a 96-token output limit. Answers were reviewed for consistency
with reference evidence and college ownership. Equivalent wording can pass;
an unnecessary fallback counts as wrong.

| Measurement | Previous adapter | New adapter |
| --- | --- | --- |
| Overall answer accuracy | 4/8 = 0.50 | 5/8 = 0.625 |
| Answers with matching evidence | 3/4 = 0.75 | 1/4 = 0.25 |
| Cross-college fallbacks | 1/4 = 0.25 | 4/4 = 1.00 |

The new adapter correctly expands the college name and refuses to transfer
engineering details to pharmacy, nursing, polytechnic, and school requests.
It unnecessarily refuses establishment year, program totals, and autonomy
questions despite matching engineering evidence.

This run does not meet the goal of answering every available college detail.

## Limits and checks

Training and evaluation question strings are disjoint. Facts and supplied
evidence can overlap, so the score measures phrasing and grounding on these
examples, not unknown facts. Validation prompts were reused from older runs;
the eight final-test prompts are new to this run and excluded from training.

The earlier 0.67 score used six different questions. Compare this run only
with the 0.50 baseline measured on these same eight questions.

Stored reference records were reused without fresh website verification.
No private conversations or invented college facts were added. Current fees,
programs and facilities require reviewed source evidence.

47 focused tests passed for dataset balance, split isolation, evidence
provenance, NLP matching, topic coverage and college scope. Adapter tensors
were checked for finite values. Tokenizer inspection confirmed that prompt
masking ends before assistant answer tokens.

## Evidence

- [Dataset manifest](training/college-scope-20261017/manifest.json)
- [Before answers and scores](training/college-scope-20261017/before.json)
- [After answers and scores](training/college-scope-20261017/after.json)

The new adapter remains inactive; chatbot configuration was not changed.
