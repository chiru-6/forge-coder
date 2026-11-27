# Forge — your local coding workbench

A coding-assistant website backed by **Qwen2.5-Coder-1.5B-Instruct** and an included, actually trained LoRA adapter. Build small functions, explain snippets, and debug basic Python or JavaScript. No paid API key is needed.

This is a small experimental fine-tune of an existing language model, not a new foundation model. Most coding ability comes from Qwen. A 60-example dataset does not make this competitive with large coding assistants.

## Run on this computer

Open PowerShell in this folder and run `./start.ps1`. The launcher uses the environment prepared alongside this project when available. After the terminal prints **Forge is ready**, open **http://127.0.0.1:8000**. Keep that terminal running; Ctrl+C stops the server.

## Set up a fresh computer

Use Python 3.11+ (this run used 3.14). Allow several GB of free disk space for PyTorch and the base model. An NVIDIA GPU with 8 GB VRAM is recommended; CPU inference works more slowly.

On Windows with an NVIDIA GPU:

```powershell
./setup.ps1
./start.ps1
```

If your PowerShell policy blocks scripts, run these individual commands instead:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install torch --index-url https://download.pytorch.org/whl/cu128
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python server.py
```

For Linux/macOS or CPU-only installation, create a virtual environment, install the appropriate PyTorch build from https://pytorch.org/get-started/locally/, then install `requirements.txt` and run `python server.py`. The application uses CUDA when available, otherwise CPU. The Windows setup script specifically installs CUDA PyTorch.

The first model load downloads Qwen from Hugging Face into `.cache/` inside this project. Later loads reuse that cache. Chat prompts are processed locally and are not sent to an API. The interface stores the current conversation in browser session storage; New conversation clears it. Only the most recent five exchanges are sent with a new message. Model inputs are capped at 2048 tokens and responses at 384 new tokens.

## What was trained

- Base: [Qwen/Qwen2.5-Coder-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct).
- LoRA: rank 8 on query/value projections, alpha 16, dropout 0.05.
- Data: 60 original synthetic examples covering 20 basic tasks; 12 validation examples covering four separate held-out tasks. Each task has three prompt variants.
- Objective: assistant-response next-token loss; user/system prompt tokens are masked.
- Training: 120 optimizer steps, effective batch size 2, AdamW at 0.0001, seed 42.
- Checkpoint: `adapter/adapter_model.safetensors`; base revision pinned in the adapter configuration.
- Measured results: [docs/training-report.json](docs/training-report.json).

The validation set is tiny. Lower validation loss does not prove better code correctness, security, or broad generalization. The Build/Explain/Debug modes also supply different system instructions; they are not three separately trained models. Review and test generated code. The server does not execute it.

## Train your own version

Edit `training/train.jsonl` with objects containing `prompt` and `response`. Keep a genuinely separate `training/validation.jsonl`. Then run:

```powershell
.venv/Scripts/python training/train.py --steps 120
```

This overwrites the adapter and training report. Back them up first if you want to keep the original. `training/make_dataset.py` recreates the bundled starter data; it overwrites both JSONL files. Extend the dataset with reviewed examples of the coding style you want before trying longer runs. Training logs report real loss; a fresh run downloads the current base revision and records it.

## Put it on GitHub

Create an empty GitHub repository, open a terminal in this project folder, then run:

```sh
git init -b main
git add .
git commit -m "Add Forge coding assistant and trained LoRA adapter"
git remote add origin https://github.com/YOUR_USERNAME/forge-coder.git
git push -u origin main
```

The `.gitignore` excludes downloaded model weights, virtual environments, and secrets. The compact LoRA adapter is included. The base model is downloaded separately at startup. Do not upload `.cache/` or your Python environment.

For a public website preview, use repository **Settings → Pages → Deploy from a branch → main → /docs → Save**. See [GitHub's Pages publishing instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

**GitHub Pages hosts only the static interface. It cannot run the Python model server.** The hosted preview displays this clearly and links to the local version. A fully online assistant needs a separate GPU/CPU server with HTTPS, authentication, rate limits, and persistent model storage. The bundled server is deliberately loopback-only and is not a public deployment server.

## Useful directions to grow

- **Python tutor:** train on reviewed explanations, edge cases, and unit tests.
- **JavaScript bug helper:** collect small broken/fixed code pairs with explanations.
- **Your coding-style assistant:** train on code you own and prefer, with secrets removed.

For more model capacity, experiment with larger [Qwen2.5-Coder variants](https://huggingface.co/Qwen) after measuring available memory. Start with the bundled 1.5B model to keep iteration quick.

## Checks and files

Run `python -m unittest discover -s tests -v` and `node --check docs/app.js`. These check request handling and JavaScript syntax without downloading a model. The HTTP tests use an explicit fake engine; they are not model-quality benchmarks. A GitHub Actions workflow runs them on pushes and pull requests.

- `docs/`: dependency-free responsive website and training report.
- `server.py`, `core.py`: local inference and input validation.
- `training/`: dataset, data generator, and repeatable training script.
- `adapter/`: trained LoRA weights and configuration.
- `requirements.txt`: supported dependency ranges.
- `requirements-tested.txt`: exact installed versions used for this run, for reference.

Original application code and synthetic examples use the MIT license. Qwen's base weights are Apache-2.0; retain their license and notices when redistributing them. This project does not bundle the base checkpoint. See `MODEL_CARD.md` for model scope and attribution.


