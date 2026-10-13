# College model training

Local preparation and model training are separate. The dataset contains public
college source text for continued language modeling. It does not contain
invented answers, private chat logs, user accounts, or feedback records.

Prepare after ingestion:

```powershell
.venv\Scripts\python.exe scripts\prepare_training.py
```

Inspect `training/audit.json`, `training/train.jsonl`, and
`training/validation.jsonl` before training. Validation sources are excluded
from the training set. Public webpages still require factual review: source
trust does not guarantee that every statement is current or correct.

On a CUDA GPU machine, copy the project, both JSONL files and the downloaded
Phi-3 model directory. Create a new virtual environment there; virtual
environments cannot be copied between machines. Install the project runtime
with a CUDA-enabled Torch build, then the training dependency:

```powershell
python -m pip install -r requirements-training.txt
python scripts/train_model.py --model /path/to/phi3-mini --data training --output .venv/models/phi3-college-adapter
```

The script trains a LoRA adapter with one epoch, batch size one and a 512-token
limit per example. Longer chunks are truncated. It records validation loss
before and after training in `training_metrics.json`. GPU memory requirements
depend on the GPU, sequence length, and software environment; this script
does not use quantization. The GPU execution path has not been verified on
this CPU-only machine.

The base model stays unchanged, and the adapter is not automatically enabled
in the chatbot. Review training metrics and test held-out college questions
before adding adapter loading to the app. Improved language-model loss alone
does not prove correct answers, and fine-tuning does not solve the CPU
inference timeout. The current chat path instead returns reviewed Q&A entries
directly and does not generate facts with this adapter.

## CPU training

Install `requirements-training.txt` in the project virtual environment. Start
with a short verification run:

```powershell
$env:HF_HUB_OFFLINE='1'
.venv\Scripts\python.exe -u scripts\train_model.py --device cpu --threads 4 --max-length 32 --max-steps 1 --eval-examples 1 --output .venv/models/phi3-cpu-test
```

For one epoch on all training examples:

```powershell
.venv\Scripts\python.exe -u scripts\train_model.py --device cpu --threads 4 --max-length 128 --eval-examples 4
```

CPU mode uses float32 frozen base weights and trains LoRA parameters. It saves
adapter checkpoints after the first step and every ten steps. Checkpoints
contain adapters, not optimizer state, and are not automatic resume points.
CPU runs may take a long time. `--eval-examples 4` is a small validation sample,
not evaluation on the entire held-out set; omit it for full validation.
Short sequences truncate source text. A one-step run only checks that training
can execute and does not constitute a trained college chatbot.
To continue from a saved adapter checkpoint, pass `--resume-from` and
`--skip-steps` for the number of already-processed training examples. Adapter
weights are restored, but optimizer state is not; training therefore resumes
with a fresh optimizer.

Phi-3 Mini may not fit in the available RAM on a CPU-only machine. A smaller
base model can be used with the same prepared dataset and training script:

```powershell
.venv\Scripts\python.exe scripts\download_model.py HuggingFaceTB/SmolLM2-360M-Instruct .venv\models\smollm2-360m-instruct
.venv\Scripts\python.exe -u scripts\train_model.py --model .venv\models\smollm2-360m-instruct --data training --device cpu --threads 4 --max-length 128 --eval-examples 4 --output .venv\models\smollm2-college-adapter
```

The script selects supported attention projection layers for LoRA based on the
loaded model architecture. The adapter remains separate from the base model
and is not automatically activated by the chatbot.

## Official college question-and-answer fine-tuning

`training/online-college-qa/` contains a small, manually reviewed Q&A set based
on the official college history page and admissions homepage. Each example
retains its source URL. The validation set holds out ranking and admissions
facts from training. Recheck time-sensitive facts against the official pages
before reusing this set.

The chat runtime uses these files as a strict verification document: it returns
the stored answer only when the normalized question exactly matches an entry.
It does not ask the language model to generate facts. Questions not present in
the files receive the admissions-contact fallback, without unrelated suggestions.
Add reviewed question variants to the dataset to expand the verified answer
coverage.

To continue fine-tuning the smaller model's existing adapter on these Q&A
examples:

```powershell
.venv\Scripts\python.exe -u scripts\train_model.py --model .venv\models\smollm2-360m-instruct --data training\online-college-qa --device cpu --threads 4 --max-length 128 --epochs 3 --resume-from .venv\models\smollm2-college-adapter --output .venv\models\smollm2-college-qa-adapter
```

This creates a separate adapter and does not change the chatbot's configured
model or activate the adapter in the app.

`scripts/run_cpu_training.ps1` runs the one-step test and then one epoch on
the dataset only if the test succeeds. Full-run progress goes to
`logs/cpu-training.log`, and errors to `logs/cpu-training-errors.log`.

CPU mixed precision follows the [PyTorch autocast documentation](https://docs.pytorch.org/docs/stable/amp.html).

## Verified CPU run on 13 October 2026

For the smaller SmolLM2 model on this CPU, `--cpu-dtype float32` performed
much faster than bfloat16. Keep bfloat16 available for the larger Phi-3 model
where full float32 weights require substantially more memory.

The latest separate Q&A adapter is
`.venv/models/smollm2-college-qa-adapter-20261013`. It was trained for one epoch
from `smollm2-college-qa-adapter-v2` using the 21-example Q&A training set,
256-token sequences, and all four validation examples. See
`TRAINING_VERIFICATION.md` for measured results and deployment limitations.

```powershell
$env:HF_HUB_OFFLINE='1'
.venv\Scripts\python.exe scripts/verify_trained_adapter.py --model .venv/models/smollm2-360m-instruct --adapter .venv/models/smollm2-college-qa-adapter-20261013
```

## Evidence-grounded NLP fine-tuning

The `grounded-nlp` dataset supplies the requested college and source evidence
with the question. It trains answers from evidence rather than memorization,
including fallback examples when another college's evidence is supplied.
Training, validation and final test questions use separate phrasings. Facts
and evidence may overlap, so the evaluation measures phrasing and grounding
on these examples, not generalization to unknown facts or colleges.

`--answer-only` masks question and context tokens from the training loss.
It rejects examples whose answer is removed by sequence truncation.

```powershell
.venv\Scripts\python.exe scripts/prepare_grounded_nlp.py
$env:HF_HUB_OFFLINE='1'
.venv\Scripts\python.exe -u scripts/train_model.py --model .venv/models/smollm2-360m-instruct --data training/grounded-nlp --device cpu --cpu-dtype float32 --threads 4 --max-length 384 --epochs 2 --answer-only --output .venv/models/smollm2-grounded-nlp-20261013
.venv\Scripts\python.exe scripts/verify_trained_adapter.py --model .venv/models/smollm2-360m-instruct --data training/grounded-nlp --split test --output training/grounded-nlp/base-test.json
.venv\Scripts\python.exe scripts/verify_trained_adapter.py --model .venv/models/smollm2-360m-instruct --adapter .venv/models/smollm2-grounded-nlp-20261013 --data training/grounded-nlp --split test --output training/grounded-nlp/adapter-test.json
```

The prompts and test conditions differ from the earlier closed-book Q&A run;
scores must not be compared as though they measured the same task. English
is the only language represented in this dataset. Adapters remain separate
and are not automatically loaded by the chatbot.
