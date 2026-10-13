# Training and database verification

Checked on 13 October 2026 (Asia/Calcutta).

## Follow-up fine-tuning and accuracy from 0 to 1

Continued the completed adapter for three more epochs (63 updates) on the
same 21 training examples. The new adapter is
`.venv/models/smollm2-college-accuracy-20261013`. CPU float32 and 256-token
sequences were used. Validation loss changed from 1.8161728140024038 to
1.7716546942637517.

Answer accuracy is `correct answers / evaluated answers`, ranging from 0
to 1. Each answer is reviewed against the reference facts; exact wording is
not required for factual correctness. Exact-match accuracy is recorded
separately.

- Reviewed answer accuracy: **0.00** (0 correct out of 4).
- Exact-match accuracy: **0.00**.
- The first answer still claims a rank band of 10; the other three answers
  omit the facts requested. None passed factual review.
- Five accuracy-calculation tests passed, covering scores 0, 0.5 and 1,
  rejection of empty evaluation sets, and rejection of unreviewed labels.
- This adapter is **not approved for activation**.

See [scored answer verification](training/accuracy-verification-20261013.json).
The four examples represent only two underlying fact topics. They were
reused to evaluate successive adapters, so this is a validation score, not
an independent final test-set accuracy estimate. Source verification limits
below continue to apply. More epochs alone did not improve factual accuracy.

## Result

CPU training completed successfully, but the new adapter **failed held-out
factual answer checks and is not approved for chatbot activation**. A lower
language-model loss did not produce reliable college answers. Keep the
existing source-grounded and verified-answer runtime in use.

## Database and datasets

- SQLite `PRAGMA integrity_check`: `ok`.
- Chroma collection `langchain`: 3,133 chunks.
- Public-source export: 1,469 training and 144 validation examples from
  442 sources; the exporter reported no shared source URLs between splits.
- 1,014 chunks were excluded by the export filters. Trusted hostnames alone
  do not establish factual correctness; the broad export requires review.
- The database contains private chat sessions and messages. These were not
  exported into model training data.
- This run used the separate `training/online-college-qa` dataset:
  21 training examples and four validation examples. No `fact_id` appears
  in both sets. The history source URL appears in both splits, so this is
  a fact-level split, not a source-level split.

Evidence: [database audit](training/audit.json).

## Completed CPU training

| Setting or measurement | Result |
| --- | --- |
| Base model | `.venv/models/smollm2-360m-instruct` |
| Starting adapter | `.venv/models/smollm2-college-qa-adapter-v2` |
| New adapter | `.venv/models/smollm2-college-qa-adapter-20261013` |
| Device / weight format | CPU / float32 |
| CPU threads | 4 |
| Epochs / completed updates | 1 / 21 |
| Maximum sequence length | 256 tokens; longer examples are truncated |
| Validation examples | All four |
| Validation loss before | 1.8348791712981003 |
| Validation loss after | 1.8161728140024038 |
| Adapter tensors | Verified present and finite |
| Automatic activation | Disabled |

This continued an existing adapter with a fresh optimizer; optimizer state
from the earlier run was not restored. It did not train Phi-3 or update the
base model. Earlier runs' metrics are separate from this run.

## Held-out answer verification

The verification script loaded the saved adapter and generated answers to
all four held-out questions using deterministic decoding and a 64-token
output limit, without giving the model retrieved source context.

| Question topic | Generated result | Assessment |
| --- | --- | --- |
| NIRF 2025 rank band | Claimed a rank band of 10 | Incorrect |
| Alternate NIRF question | Invented approval and award steps | Unsupported |
| Admissions levels and subjects | Listed only Bachelor of Science | Incomplete and unsupported as an answer to the question |
| Programs advertised | Produced an introduction with no program list | Incomplete |

Exact matches: **0 of 4**. This tiny sample is not a general accuracy estimate.
The qualitative failures above are the reason activation is rejected.
Raw generated and expected answers are preserved in
[verification results](training/verification-20261013.json).

## Source verification limits

The [official admissions page](https://admissions.egspgroup.in/) was accessible
and states undergraduate, postgraduate and doctoral programs in Engineering,
Management and Science. It also displays a NIRF 2025 band of 201–300.

The [college history page](https://egspec.org/about/history) returned a
bot-verification screen during this check. The historical claims in the
stored training set were therefore not independently reverified today.
Do not label the entire dataset factually verified on the basis of this run.

## Application checks

Ten selected tests passed: verified college answer matching, verified chat
policy, database behavior, and text processing. These tests check application
behavior, not the trained model's factual accuracy. Existing API answer
paths can return stored source-backed answers without activating this adapter.

## Reproduce

```powershell
$env:HF_HUB_OFFLINE='1'
.venv\Scripts\python.exe scripts/prepare_training.py
.venv\Scripts\python.exe -u scripts/train_model.py --model .venv/models/smollm2-360m-instruct --data training/online-college-qa --device cpu --cpu-dtype float32 --threads 4 --max-length 256 --epochs 1 --resume-from .venv/models/smollm2-college-qa-adapter-v2 --output .venv/models/smollm2-college-qa-adapter-20261013
.venv\Scripts\python.exe scripts/verify_trained_adapter.py --model .venv/models/smollm2-360m-instruct --adapter .venv/models/smollm2-college-qa-adapter-20261013
```

The training command writes to its output directory. Choose a new output path
to preserve this run. More training is not guaranteed to correct these failures;
review the source facts and use retrieval to supply authoritative evidence.
