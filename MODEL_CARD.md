# Forge Coder — experimental LoRA adapter

Base model: [Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct), by the Qwen team, Apache-2.0.

Pinned base revision: `2e1fd397ee46e1388853d2af2c993145b0f1098a`.

This project adapts the base model using PEFT LoRA. It does not claim authorship of Qwen's architecture, tokenizer, pretraining data, or base weights. The distributed adapter contains 1,089,536 trained parameters. The full model has approximately 1.5 billion parameters.

## Intended use

Local experimentation with small coding requests and the mechanics of fine-tuning. Basic Python and JavaScript examples are the training focus. Explain and Debug modes add system instructions at inference time. Generated code must be reviewed and tested.

## Training data and method

The included synthetic data was authored for this project without scraping repositories. There are 20 training tasks and 4 held-out tasks, each expanded into 3 prompt variants: 60 training rows and 12 validation rows. Validation task solutions do not occur in the training split. Some concepts and style naturally overlap. Dataset source is visible in `training/make_dataset.py`.

Training uses response-only cross-entropy, rank-8 LoRA on query/value projections, alpha 16, dropout 0.05, AdamW at 1e-4, effective batch size 2, and 120 optimizer steps. It ran on an NVIDIA GeForce RTX 4060 Laptop GPU with BF16. Optimizer loop plus final validation/save took 53.19 seconds, excluding dependency installation, download, model loading, and initial validation.

## Observed results

Token-weighted held-out response loss was **1.5029215614 before** and **0.7740033684 after** fine-tuning. The adapter was evaluated with dropout disabled. Full step logs and settings appear in `docs/training-report.json`.

This is a tiny, related-domain validation set, not a coding benchmark. No claim is made about improvement on HumanEval, SWE-bench, unseen repositories, security-sensitive programming, or general coding accuracy. The fine-tune may reduce performance outside its training style. No independent safety evaluation was performed.

## Limitations

The small model can invent APIs, misdiagnose bugs, produce invalid code, or give incorrect explanations. It has no repository access, terminal execution, browsing, retrieval, or knowledge of your files unless pasted into the prompt. The bundled app limits inputs to 2048 tokens and outputs to 384 tokens; long answers may be cut short. Do not treat it as an autonomous coding agent.

## Distribution

Only the adapter is bundled; base weights download from Hugging Face. Original application source, synthetic examples, and original adapter contribution are provided under the included MIT license; the upstream model's Apache-2.0 terms and notices remain applicable to the upstream materials. Retain upstream notices if distributing merged weights.


