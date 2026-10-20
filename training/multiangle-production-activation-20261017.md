# Multi-angle production adapter activation

- Base model: `smollm2-360m-instruct`
- Previous adapter: `smollm2-egs-balanced-production-20261017`
- Active adapter: `smollm2-egs-multiangle-production-20261017`
- Training: 40 continuation LoRA steps, answer-only loss, learning rate `2e-5`
- Dataset: 170 train, 22 validation, 8 held-out test examples
- Added coverage: 36 multi-angle questions across all 8 institutions
- Validation loss: `0.0187139` before, `0.0138067` after
- Adapter integrity: 256 finite tensors
- Held-out over-rejection: 0 of 8 institution questions
- Production verified-RAG audit: 36 of 36 passed
- Regression suite: 49 of 49 passed

Long enumerations remain protected by the verified-answer/RAG layer because the
standalone 360M model can truncate or repeat items in long lists. Production
activation therefore retains source-owned deterministic answers ahead of model
generation.
